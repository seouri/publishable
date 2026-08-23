# H6b — the environment record and the diagnostic debt — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `run.yaml` gains `provenance.environment.os`, `.hostname` and `.hardware` — the last live row
of the six-unwritten-keys filing — `study add`'s waiting `hostname` redaction gets a record written by a
real run and the two keys it must **not** redact get a stated reason and a pin, and the two shipped
codes the git layer raises (`E-GIT-NO-REPO`, `E-GIT-NO-COMMIT`) get their first § Errors rows.

**H6b is additive, and the claim was measured rather than framed.** No shipped key's contents move.
`grep -n "hash(provenance\|hash(run_doc\|hash(record" src/publishable/*.py` at `2b18435` returns
nothing, and the `provenance` mapping is built long after every hash is folded — so three new keys
cannot move `code_hash`, `parameters_hash`, `input_manifest_hash`, `uv_lock_hash`, `units_hash`,
`allocation_hash` or `design_digest`. Guard-pin arms Q and U are what turn that sentence into a test.

**H6b moves NO row of the four-row table and mints no fifth number.** Task 11 repeats it character for
character, per design Decision 15, which **derived** that rather than assuming it.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**That table is reproduced here for a reader's convenience and is NOT this plan's source of truth for
it** — task 11 copies it out of the feasibility analysis' own last entry with `sed` and diffs against
that extraction. Reproducing it in a plan and then trusting the reproduction is how both of that
analysis' wrong figures were made. **No task may write "N configs now execute" or mint a fifth number.**

**Architecture.** No new module, no new file of any kind. Two source files, one test file's docstring,
and five documents move.

- **`cli.py`** — three stdlib imports (`os`, `platform`, `socket`; none is imported today, grepped) and
  three keys in `command_run`'s one `environment` dict literal.
- **`secrets.py`** — one docstring enumeration **deleted**.
- **`study.py`** — `_redact`'s docstring rewritten to the fact it now describes.
- **`docs/reference.md`** — § The two files (the `hardware` line and the GPU sentence), § What
  `study add` redacts (the reason), § Errors core raises (two rows), § Templates (re-read, and edited
  only if the measurement says so).
- **`docs/superpowers/spec-defects.md`** — one entry closed, three amended, two filings.
- **`docs/feasibility-llm-growth-studies.md`** — one appended § Executability entry.
- **`CLAUDE.md`** — the slice entry and the order line.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. Tests land in existing modules —
`tests/test_cli.py`, `tests/test_study.py`. **No task creates a file**, so `ruff format --check` stays
at **93** and `mypy` at **52 source files** at every commit.

**Spec:** `docs/superpowers/specs/2026-08-23-environment-record-design.md` — read it beside this plan,
including its § Corrections to the charter, § The guard pin, § The fixtures, § The mutations, and
§ What this slice refuses to build. **Its body must not be edited.** Where this plan measured something
that contradicts it, the disagreement is in [§ Corrections against the code](#corrections-against-the-code),
appended by this plan's author and extended by no task.

**Measurement this plan argues from:** `docs/superpowers/H6-SCOPING.md`, measured 2026-08-22 against
`da9907b` — **written before H6a merged, and three of its eight rows are stale in consequence**, which
the design's § Corrections to the charter enumerates and this plan re-checked. Every signature,
literal and message below was read or **run** at `main`'s HEAD, **`2b18435`**. **Nothing is cited by
line number.**

**Baseline at `2b18435`, and how each figure was obtained:**

- `uv run pytest -q` → **2963 passed, 1 skipped, 2 xfailed** in 193 s — run in the foreground, in the
  real repo, on a clean tree.
- `uv run pytest --collect-only -q` → **2966 collected** (2963 + 1 + 2 = 2966, so the two agree).
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **93 files already formatted**
- `uv run mypy` → **Success: no issues found in 52 source files**

**Task count: 11.** The scoping charters eight; the design's § Corrections to the charter derives 11.
11 tasks make 11 commits.

---

## Sequencing

**Execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11.** Numeric and execution order
coincide in this slice; a controller looking for `## Task N` finds it in position N.

| Constraint | Why |
|---|---|
| **Task 1 before every other task** | Arm P must be captured before the key set moves, and **five of six arms have no authorized editor** |
| **Task 2 before task 3** | The documents lead. `hardware`'s shape is written into § The two files before code writes a mapping with that shape |
| **Task 3 before task 4** | Fixture E needs a real run whose record carries the three keys. Before task 3 it would assert nothing |
| **Task 5 after task 1** | It documents behaviour arm T pins; writing the rows first would be writing them against unpinned behaviour |
| **Task 6 after tasks 1–5** | Ruling P's confirmation is a measurement against the code **as H6a left it**, and Decision 12's decline is stated once every other H6b question is answered — the filing asks for the two to be decided together |
| **Task 7 after task 3** | Two of the three claims are made false **by** task 3; editing them first would be editing a true sentence into a false one and back |
| **8, 9, then 10, then 11** | Every filing against the finished branch; both consistency passes after the last document edit; the § Executability entry last so its commit sha is the branch's |

### One deviation from the design's grain, argued

**The design's task 3 writes all three keys.** The scoping gave them three tasks (13, 14, 15). They
write into **one** dict literal and each invalidates **one** shipped exact-key-set assertion — arm P.
Splitting them would edit that arm three times, which is exactly the shape *a pin that must move is
moved once, by a named task* exists to prevent, and which H6a's batch-2 Major cost a round-trip. **One
task, one editor, one edit.**

---

## Batching — six batches, one report and one review each

**Every batch gets a review, including the last.** Twice a controller ran a slice's final batch
straight into the whole-branch gate, and the second time **three of four whole-branch Majors lived in
it** — a documents-and-records batch looks like the safest one to skip and is the one whose output no
later batch reads.

| Batch | Tasks | What its review must be able to see |
|---|---|---|
| **B1 — the pin and the document that leads** | **1, 2** | Does every arm name a sole editor or an explicit **NONE**? Is arm P's post-edit state written in the shape Ruling O decided — `hardware` a **mapping**, asserted as `set(hardware) == {"cpu_count"}`, not a scalar? Was arm R proven unaffected by extracting `_H5A_ARM_D_LITERALS` and testing the `hardware:` line against every member, rather than by reading? Was arm T demonstrated able to fail? Does § The two files' edit **link** to § The apparatus core can only observe rather than restating it, and does the worked example still record `apparatus: null`? Mechanical pass on the `reference.md` edit |
| **B2 — the write** | **3** | **A real-command review**: run the installed console script on a project outside this repo and read `run.yaml` key by key. Is arm P's edit **exactly** three pops plus three assertions, with the `assert environment == {...}` line byte-identical? Are arms Q, R, S and U green **without** an edit? Does Fixture A install sentinels rather than recomputing the composition? Does Fixture C have **both** arms? Run mutation 6 and confirm it fails Fixture D and **passes** arm P, as the design claims |
| **B3 — the redaction pin and the two rows** | **4, 5** | Does Fixture E assert **both** halves against the **source** record read from the run directory, and is the bundle built **outside** any repository? Does each new § Errors row carry the two surfacing paths, the three deliberate swallows, and the **cwd** walk-up? Was the table's own **scope sentence and column header** checked, rather than this plan's instruction — H6a's batch 4 settled that question by citing a design and was wrong to? Does Fixture G read **both** ends, or does it compare the table with itself? |
| **B4 — the two rulings decided together, and the stale claims** | **6, 7** | Was § Templates' **whole paragraph** re-read against the code as H6a left it, including the *"no ignore file could have done that for it"* clause Ruling F made false — and was the finding reported as a `git status` measurement before and after a real `validate`, not as an assertion? Is Decision 12 recorded as a **decline with a reason and a re-owning**, never as a strike? Was `secrets.py`'s enumeration **deleted** rather than rewritten? |
| **B5 — the records** | **8, 9** | Every closed or amended entry checked against the code; every "filed" checked against the file; every owner a fact with a reason and never *"whichever slice next touches X"*. Is the six-unwritten-keys entry closed only because **every** row of its table is closed? Does `CLAUDE.md`'s order line lose H6b and keep H9 and H3c-3's 14? |
| **B6 — the passes and the entry** | **10, 11** | **A full review, not a skim.** Every sweep **names its files**, never filters its output, is **newline-insensitive**, and is **proven able to fail** against a string known to be present. Four rows character for character, extracted with `sed` and diffed; **no fifth number**; the derivation printed ahead of the table |

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`. Types
`uv run mypy`. All four must pass before a commit. **Baseline at `2b18435`: 2963 passed, 1 skipped, 2
xfailed; 2966 collected; 93 files formatted; 52 source files typed.**

**No gate literal moves in this slice.** No task creates a file, so `ruff format --check` stays **93**
and `mypy` stays **52 source files** at every commit. **Every task states its own DELTA on the test
count, not an absolute**; compute the absolute from your own previous run and reconcile any difference
before committing.

**Run `uv run pytest` DIRECTLY, in the foreground, and wait for it.** It takes about three and a quarter
minutes at this baseline. **Never construct a wait, a monitor, a poll or a background run around it** —
agents on preceding slices stalled that way and one stopped with a mutation still applied.

**Never `git checkout -- <file>`.** It destroys uncommitted work and has been mistaken for reverting a
mutation twice in this repo. Copy the file before mutating, restore from the copy, and **verify the
revert by behaviour** — never by `git status`, and least of all by an account of what caused the change.

**A mutation's silence is evidence about the tests, not about the code.** If a mutation you were told
to run changes nothing, say so and build the discriminating test; do not conclude the code is
unreachable. Twice in one slice an agent emptied a payload, watched the suite stay green, and concluded
the payload was unreachable — while a discriminating test was available both times.

**Do not report a count of zero disagreements.** Before writing *"no existing test asserts X"*, or
repeating any claim this plan or your brief makes about the code, **grep for it and report what you
grepped**, newline-insensitively — flatten whitespace before matching, because a `grep -F` cannot match
a wrapped phrase. Six consecutive slices' reports claimed zero and all six were wrong, and every one
hid in a claim about **other tests or other rows**.

**Never filter the output of a sweep whose job is to find a string** — filter the file list. A reviewer
checking this exact rule lost a true hit to `grep -v superpowers`, because the matching line contained
that path. **Prove every sweep can fail** by running it against a string known to be present. The
development record is tracked, so a sweep over the four documents must **name** them: `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`.

**A comment or docstring claiming a guarantee is a claim, and needs a mutation like any other.** If a
comment says *this cannot happen*, make it happen. **Prefer deleting a claim to rewriting it** — a
rewrite invents; a deletion cannot.

**Cite by section, never by line number.** `×` not `x` for multiplication. Hyphens, never en dashes, in
anything that becomes a filename or an anchor. **No positional row locators** — never *"the two rows
above"*; name what a sibling row **does**. **Today is 2026-08-23.**

**`scripts/sdd-workspace` rewrites `.superpowers/sdd/.gitignore` to a bare `*` every time it runs, and
`task-brief` calls it.** Restore that file's content when you notice it, and use `git add -f` when
committing new records.

**`ruff format` does not touch `*.md`.** Two agents on two slices have blamed it for rewriting a
document's fenced Python block, and both then reverted files on that reading; measured both times as
byte-identical. If a document changes under you, **find what did it** rather than reverting on a story.

---

## Task 1: the guard pin — six arms, captured before anything moves

> **Bindings that reach this task:** design Decision 16 (the pin's shape), **Ruling O** (restated
> below, because `hardware`'s shape decides arm P's advance spec and `task-brief` extracts this section
> and nothing else).

**RULING O, restated here in full:** `provenance.environment.hardware` carries **`cpu_count` and NOT
`gpu`**. It is a **mapping** — `{"cpu_count": <int|None>}` — because § The two files shows a mapping
and because `os.cpu_count()` can answer `None`. A GPU is an **apparatus fact**, not a provenance key.
**This decides arm P's advance spec:** the assertion is `set(hardware) == {"cpu_count"}`, never
`isinstance(hardware, int)`. H6a's batch-2 Major was a pin captured against a **superseded signature**,
which forced the next task to choose between a broken import and an unauthorized edit; capturing arm P
in a shape Ruling O has already decided is what prevents the same round-trip here.

**Six arms. Five have NO authorized editor.** The device's whole value is that a passing arm is the
proof. **An implementer may not self-authorize an edit to an arm with no authorized editor, even when
the edit is mechanical and even when it turns out clean** — the route is a controller ruling, which
costs one round-trip and preserves the thing the arm exists for.

| Arm | Where it lives | Sole authorized editor | Advance spec |
|---|---|---|---|
| **P** | `tests/test_cli.py::test_h8b_arm_d_the_five_figures_diff_reads` (exists; H8b's) | **task 3 only** | The `assert environment == {"manager": "uv", "uv_lock": None, "uv_lock_hash": None}` line is **byte-identical after the edit**. Task 3 adds exactly three `.pop(...)` calls and exactly three assertions, listed in task 3 |
| **Q** | `tests/test_cli.py::test_h8b_arm_c_the_records_key_lists_status_and_exit` (exists) | **NONE** | unchanged, byte for byte |
| **R** | `tests/test_cli.py::test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` (exists) | **NONE** | unchanged, byte for byte |
| **S** | `tests/test_study.py::test_study_add_redacts_hostname_when_present_on_a_synthesized_record` and `test_study_add_leaves_hostname_untouched_when_absent_from_the_source` (exist) | **NONE** for the test bodies; task 7 edits `_fixture_y_record`'s **docstring only** | both bodies unchanged; the docstring edit is named in task 7 so it is not read as an arm edit |
| **T** | **NEW**, `tests/test_cli.py` | **NONE** | written by this task, green against today's behaviour, unchanged thereafter |
| **U** | `tests/test_cli.py`'s `_h6a_pin_project` arms — H6a's own literal digests | **NONE** | unchanged. They assert individual keys, so the three insertions are invisible to them — **which is the additive claim, and a passing arm is the proof** |

**Steps**

- [ ] Re-confirm the baseline with one foreground `uv run pytest -q` and reconcile any difference from
      *2963 passed, 1 skipped, 2 xfailed* **before** doing anything else.
- [ ] **Locate arms P, Q, R, S and U by test name** (`grep -n` for each name) and **add one sentence to
      each docstring** naming its H6b authorization: *"H6b guard-pin arm \<X\>: sole authorized editor
      \<task N | NONE\>."* This is the only edit this task makes to an existing test, it adds no
      assertion and moves no literal, and the report must show the `git diff` line count per arm.
- [ ] **Prove arm R is unaffected by Ruling O's edit** before task 2 makes it: extract
      `_H5A_ARM_D_LITERALS` from `tests/test_cli.py` and test each member against the literal string
      `    hardware: {gpu: "1x A100 80GB", cpu_count: 32}`. **Report the members and the result.** This
      plan measured **no member matches**; a different answer is a disagreement to report, not to
      absorb.
- [ ] **Write arm T** — new coverage. `grep`ped newline-insensitively over every file in `tests/` for
      both codes at `2b18435`: **nine hits, none through `main([...])`** — two direct calls in
      `tests/test_provenance.py`, four monkeypatched raises in `tests/test_validate.py`, one docstring
      each in `tests/test_lineage.py` and `tests/test_study.py`. **Re-run that grep and report it**
      rather than repeating this sentence.

Arm T, three invocations, all measured at the console script before this plan was written:

```python
def test_h6b_arm_t_the_git_layers_two_codes_at_the_cli(tmp_path, capsys, monkeypatch):
    """H6b guard-pin arm T: SOLE AUTHORIZED EDITOR — NONE.

    New coverage. Both codes are raised by `provenance.py` and neither is
    asserted through `main([...])` anywhere in `tests/` at `2b18435`
    (grepped newline-insensitively: nine hits, all direct calls,
    monkeypatched raises, or docstrings). H6b task 5 documents these two
    codes and changes no behaviour, so this arm is what makes the two new
    § Errors rows checkable against behaviour rather than against prose.

    Measured at the installed console script before it was written:
      * `run` on a project whose `.git` was removed  -> E-GIT-NO-REPO, exit 1
      * `generate experiment` with cwd outside a repo -> E-GIT-NO-REPO, exit 1
      * `run` in a `git init`-ed repo with no commit -> E-GIT-NO-COMMIT, exit 1,
        and NOT E-CODE-DIRTY, even though both hashed trees are untracked
    """
```

- [ ] Build arm T's three invocations from `tests/test_cli.py`'s existing project helper. For each:
      assert the exit code is `EXIT_WRONG`, assert the code string appears in **`capsys`' err
      stream** (`main`'s `except PublishableError` prints to stderr — asserted on the stream the thing
      writes to, not on combined output), and for the third **additionally assert `"E-CODE-DIRTY"` is
      absent**, which is the ordering claim design Decision 3's row makes.
- [ ] **Prove arm T can fail.** Run mutation 11 — reorder `provenance.git_provenance` so the dirty
      computation precedes the `HEAD` check — against a **copy** of `provenance.py`, confirm the third
      invocation fails on the `E-CODE-DIRTY`-absent assertion, restore from the copy, and re-run the
      test to confirm it passes again. **Verify the revert by behaviour.**
- [ ] `uv run pytest`, `ruff check`, `ruff format`, `mypy`. **Delta: +1 test** (arm T). Commit.

**What this task must NOT touch.** `src/` — nothing at all. Any assertion, literal or name inside arms
P, Q, R, S or U. `docs/`. The three keys themselves: this task writes no production code.

---

## Task 2: Ruling O written into § The two files — `hardware: {cpu_count: 32}`, and where a GPU goes instead

> **Bindings that reach this task:** **Ruling O**, restated in full below. The documents lead, so this
> task lands before the code that implements it.

**RULING O, restated here in full:** `hardware` carries **`cpu_count` and NOT `gpu`**. Grounds, from
`CLAUDE.md` § Invariants' core-vs-plugin test — *would it be identical for a wet-lab assay, a
simulation sweep, and an LLM benchmark?* — a CPU count is `os.cpu_count()`, stdlib, answerable
everywhere; a GPU is not, and core cannot probe one without a dependency or a subprocess. **The
apparatus is the existing route for anything core cannot observe**, and H7d Parts A and B built it for
exactly this. **§ The two files shows `hardware: {gpu: "1x A100 80GB", cpu_count: 32}`, and that
example must change.** This task's ruling is **which way**: the `gpu` **fact leaves the example**, and a
sentence naming the apparatus as its route replaces it.

**Why not the other way — measured, so the reader can check it.** Sourcing `gpu` from the apparatus
*inside* that example would give the worked example a probe. § The apparatus core can only observe says
*"An experiment whose measurements never leave the machine declares nothing and records `apparatus:
null` — **the worked example throughout this document is one**"*, and the same `run.yaml` example
carries `apparatus: null   # no probe declared`. Changing that is a change to the shared worked example
`CLAUDE.md` § The worked example governs, and Ruling O does not authorize it.

**Cost if wrong, and it goes in the document rather than only here.** *A reader of a bundle cannot tell
what hardware produced a number unless the producer declared an apparatus probe.* That is the trade
this project makes everywhere else, and **it must be stated beside the change rather than hidden**.

**Steps**

- [ ] In `docs/reference.md` § The two files, change the one line
      `    hardware: {gpu: "1x A100 80GB", cpu_count: 32}` to `    hardware: {cpu_count: 32}`.
      **Nothing else in that fenced block moves** — `os`, `hostname`, `manager`, `python_version`,
      `uv_lock` and `uv_lock_hash` keep the values and the comments they already carry, and
      `apparatus: null` stays.
- [ ] Add, in the prose that follows the block, **one** short passage: that `hardware` carries the CPU
      count core can read on any machine and nothing else; that a GPU, an instrument revision or a
      hosted model deployment is an **apparatus fact** and **link** to § The apparatus core can only
      observe rather than restating what that section says; and the cost, stated — a reader cannot tell
      what hardware produced a number unless the producer declared a probe.
- [ ] **Sweep for `gpu` and for `A100` over the four documents named individually** — `README.md`,
      `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md` — and over
      `CLAUDE.md`. Filter the **file list**, never the output. **Prove the sweep can fail** with a
      control string known to be present in each file. Report every hit and what you did about it.
      This plan measured: `gpu`/`A100` appear in `docs/reference.md` only at the line being edited, and
      in `tests/test_report.py` as **apparatus** fixture facts, which are correct and must not move.
- [ ] Mechanical pass on the edited file: every relative link and `#anchor` resolves, no two headings
      produce the same anchor, every table row matches its header's column count, no trailing
      whitespace, tab or invisible unicode, fenced blocks skipped in all of it.
- [ ] Run **arm R** and report that it passes **without an edit**. If it fails, stop: Ruling O's edit
      touched a worked-example literal and that is a finding for the controller, not something to fix
      by editing an arm with no authorized editor.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** `src/`. `tests/` — arm R is **run**, never edited. Any other key of
the `environment` block in the example. § What `study add` redacts (task 4's). § Errors core raises
(task 5's). § Templates (task 6's).

---

## Task 3: THE WRITE — `os`, `hostname` and `hardware` in one dict literal

> **Bindings that reach this task:** **Rulings O and Q** and design Decisions 6–9, all restated below.
> **This task is arm P's SOLE AUTHORIZED EDITOR**, and its post-edit state was written in task 1 before
> anything moved.

**RULING O, restated:** `hardware` is `{"cpu_count": os.cpu_count()}` — a **mapping**, one key, **no
`gpu`**. A GPU is an apparatus fact.

**RULING Q, restated (it binds this task by what it forbids):** `os` and `hardware` are **NOT** redacted
by `study add`; `hostname` **is**. So this task **writes all three plainly** and touches
`study.py`'s `_redact` **not at all** — the wiring for `hostname` already exists and was written
against a key nobody wrote. Task 4 owns the reason and the pin.

**Decision 6 — `os` is the composed form.** `f"{platform.system()}-{platform.release()}-{platform.machine()}"`,
**not `platform.platform()`**. Measured on the design's machine: `platform.platform()` returns
`'macOS-26.5.2-arm64-arm-64bit-Mach-O'` — the marketing name and version rather than the kernel the
same module's `uname()` reports (`Darwin`, `25.5.0`) — and its component count differs per platform
(`-with-glibc2.35` on Linux). `platform.platform(terse=True)` returns `'macOS-26.5.2'`, dropping the
architecture entirely. The composed form yields exactly three components everywhere and is the shape
§ The two files shows (`os: "Linux-6.8.0-x86_64"`).

**Decision 7 — `hostname` is `socket.gethostname()`.** **The sibling that already got it right is the
first place to look**: `src/publishable/run_identity.py` already writes
`json.dump({"host": socket.gethostname(), "pid": os.getpid()}, fh)` into the run lock. Using
`platform.uname().node` would be a second spelling of one fact, which is what `report`'s `repo_root`
row rejects by name (*"two sources for one fact is how the two drift"*).

**Decision 8 — `cpu_count` is `os.cpu_count()` and `None` is written through.** Not `or 1`, not `or 0`.
`os.cpu_count()` is documented to return `None` when the count is indeterminable, and this format
already spells never-captured as `null` (`apparatus: null`, `uv_lock: null`, `units: null`).
`len(os.sched_getaffinity(0))` is **absent on the design's platform** (measured), so it cannot be the
source, and a present-or-fallback scheme would make the key mean two things on two machines.
`os.process_cpu_count()` is 3.13+ and this project targets ≥ 3.11.

**Decision 9 — the key order is § The two files' own.** `manager`, `python_version`, `os`, `hostname`,
`uv_lock`, `uv_lock_hash`, `hardware`.

**The code.** `cli.py` imports **none** of `os`, `platform` or `socket` today — grepped at `2b18435`
for `\bos\.`, `\bplatform\.`, `\bsocket\.` and `import os\b`: **zero hits**. Add the three to the
stdlib block, keeping it alphabetical (`dataclasses`, `importlib`, `importlib.metadata`, `json`, `os`,
`platform`, `socket`, `sys`).

The `environment` value in `command_run`'s `provenance` mapping becomes:

```python
            "environment": {
                "manager": "uv",
                "python_version": ".".join(str(v) for v in sys.version_info[:3]),
                # NOT `platform.platform()`: measured, it reports the marketing
                # name and version (`macOS-26.5.2-arm64-arm-64bit-Mach-O`) rather
                # than the kernel `uname` names (`Darwin`, `25.5.0`), and its
                # component count differs per platform. The composed form yields
                # exactly three components everywhere, which is the shape
                # `reference.md` § The two files shows.
                "os": f"{platform.system()}-{platform.release()}-{platform.machine()}",
                # `socket.gethostname()` and not `platform.uname().node`, which
                # returns the same fact: `run_identity` already answers "what
                # machine is this" this way for the run lock, and two spellings of
                # one fact is how the two drift. Redacted by `study add`.
                "hostname": socket.gethostname(),
                "uv_lock": "environment/uv.lock" if lock_path is not None else None,
                "uv_lock_hash": lock_hash,
                # `cpu_count` alone. A GPU is not universal and core cannot probe
                # one without a dependency or a subprocess, so it is an apparatus
                # fact — `reference.md` § The apparatus core can only observe.
                # `None` is `os.cpu_count()`'s own documented answer for
                # indeterminable and is written through rather than substituted:
                # this format already spells never-captured as `null`.
                "hardware": {"cpu_count": os.cpu_count()},
            },
```

**Steps**

- [ ] Add the three imports and the three keys, exactly as above, in exactly that order.
- [ ] **Edit arm P, and only as specified in task 1.** After `python_version` is popped, add exactly
      three pops and exactly three assertions:

```python
    os_value = environment.pop("os")
    hostname = environment.pop("hostname")
    hardware = environment.pop("hardware")
    assert environment == {"manager": "uv", "uv_lock": None, "uv_lock_hash": None}
    assert isinstance(python_version, str) and python_version
    assert isinstance(os_value, str) and os_value
    assert isinstance(hostname, str) and hostname
    assert isinstance(hardware, dict) and set(hardware) == {"cpu_count"}
```

      **The `assert environment == {...}` line is byte-identical to what task 1 captured.** Report the
      `git diff` for that test and confirm it: three pops added, three assertions added, nothing else.
      Editing the `==` literal, `python_version`'s pop, or any other assertion is a finding.
- [ ] **Fixture A — `os`, with installed sentinels.** Monkeypatch `platform.system` → `"Fixtureos"`,
      `platform.release` → `"9.9.9"`, `platform.machine` → `"fixarch"`; run a project end to end
      through `main(["run", …])`; assert `provenance.environment.os == "Fixtureos-9.9.9-fixarch"`.
      **Sentinels rather than recomputing the composition in the test**: a test that recomputes
      `f"{platform.system()}-…"` and compares is *a mutation whose two branches cannot differ* — it
      would pass against any implementation using the same three calls in any order.
- [ ] **Fixture B — `hostname`.** Monkeypatch `socket.gethostname` → `"pinhost.example.invalid"`;
      assert the record carries that string verbatim. Discriminating against the plausible wrong
      source: `platform.uname().node` is unaffected by this patch.
- [ ] **Fixture C — `hardware`, TWO arms.** Arm 1: monkeypatch `os.cpu_count` → `77`, assert
      `hardware == {"cpu_count": 77}`. Arm 2: monkeypatch it → `None`, assert
      `hardware == {"cpu_count": None}` — **the key present with a null value**, not the key absent.
      One arm cannot distinguish "writes the count" from "writes a constant"; arm 2 is what catches
      `os.cpu_count() or 1`.
- [ ] **Fixture D — the key order.** Assert
      `list(record["provenance"]["environment"]) == ["manager", "python_version", "os", "hostname",
      "uv_lock", "uv_lock_hash", "hardware"]`, read from `yaml.safe_load` of the raw file.
      **Enumerate the literals the list should contain** — never iterate the thing under test, which is
      how a vocabulary test once measured only that a set equals itself.
- [ ] **Run every mutation and report each result**, each against a **copy** of the file:
      **1** delete `"os"` → Fixtures A and D fail, arm P fails.
      **2** compute `os` as `platform.platform()` → Fixture A fails. *Checked in advance that the two
      branches can differ:* `platform.platform()` resolves `system`/`release`/`machine` through
      module-global lookup, so Fixture A's patches reach it, and it appends further components — and if
      its memo was warmed earlier it returns the machine's real string. Neither equals the sentinel
      composition.
      **3** read `hostname` from `platform.uname().node` → Fixture B fails on every machine.
      **4** write `hardware` as the bare int → Fixture C arm 1 and arm P fail.
      **5** write `os.cpu_count() or 1` → **only Fixture C arm 2** fails; arm 1 passes identically,
      which is why arm 2 exists.
      **6** swap `os` and `hostname`'s insertion order → **Fixture D fails and arm P passes**. Report
      both halves: if arm P also fails, this plan's claim that arm P is order-blind is wrong and that
      is a disagreement to report.
- [ ] **Run the installed console script end to end** on a project outside this repo and read
      `run.yaml` **key by key** against the block above. A direct call is not this step: the value is
      written by `command_run` and read by nothing, so only a real record proves it lands.
- [ ] Run arms Q, R, S and U and report that each passes **without an edit**.
- [ ] Four gates. **Delta: +5 tests** (Fixture A, B, C×2, D). Commit.

**What this task must NOT touch.** `study.py` — Ruling Q is task 4's, and `_redact` needs no change.
`docs/` — nothing. Arms Q, R, S, U: run, never edit. Arm P beyond the three pops and three assertions.
`secrets.py`'s docstring (task 7's, and it is false **today** rather than made false here).

---

## Task 4: Ruling Q — the reason in § What `study add` redacts, and the end-to-end bundle pin

> **Bindings that reach this task:** **Ruling Q**, restated in full below. It is the whole of this task.

**RULING Q, restated here in full:** `os` and `hardware` are **NOT** redacted by `study add`;
`hostname` **is**. Grounds: redaction exists for **identity and credentials**, and a bundle reader needs
to know what platform produced a number — that is provenance, not exposure. `hostname` names a machine
and often a person; `os` and `cpu_count` name neither. **Record the reason in § What `study add`
redacts** so the next reader does not re-litigate it, **and pin that a bundle carries them
unredacted** — the `hostname` redaction wiring already exists and was written against a key nobody
wrote, so **the pin is the point** for all three.

**Steps**

- [ ] In `docs/reference.md` § What `study add` redacts, add the **reason** — not two table rows. The
      table's four rows stay four. The passage says: `provenance.environment.os` and `.hardware` travel
      **unredacted** and why — a platform string and a core count name neither a person nor an
      institution, and *what platform produced this number* is provenance, which is what a bundle
      exists to carry; the same line the section already draws for `input_manifest_hash`, which
      survives while its path does not. Say it once, in the section that owns it.
- [ ] **Fixture E — end to end, BOTH halves.** Run a real project. `study new` a bundle **under
      `tmp_path`, outside any repository** — measured: `study new` and `study add` both refuse a bundle
      path inside a git repo (`E-STUDY-IN-REPO`, `provenance.find_repo_root` succeeding is the
      refusal). `study add` the run's `run.yaml`. Then read **both** records — the bundled member and
      the **source** `run.yaml` from the run directory — and assert:

```python
    assert bundled["provenance"]["environment"]["hostname"] == REDACTED
    assert bundled["provenance"]["environment"]["os"] == source["provenance"]["environment"]["os"]
    assert isinstance(bundled["provenance"]["environment"]["os"], str)
    assert bundled["provenance"]["environment"]["os"]
    assert (
        bundled["provenance"]["environment"]["hardware"]
        == source["provenance"]["environment"]["hardware"]
    )
    assert isinstance(bundled["provenance"]["environment"]["hardware"], dict)
```

      **The source record is the positive control.** Comparing against a value the same run produced
      means an implementation that wrote nothing fails **both** halves, where a bare `is not None`
      would pass on an empty string. Asserting only the redaction would leave the not-redacted half
      untested, and *a control asserting only absences passes identically if nothing ran*.
- [ ] **Run both mutations and report each:**
      **7** make `_redact` also redact `os` → the verbatim half fails and the **redaction half still
      passes**, which is why both live in one block.
      **8** make `_redact` stop redacting `hostname` → the redaction half fails **and** arm S's
      synthesized-record test fails. Report both, from a real record and a hand-built one.
- [ ] Run arm S and report that both its tests pass **without an edit**. Fixture E is added **beside**
      the synthesized record, never in place of it: the hand-built record still exercises every
      redacted field at once, and the real record exercises the wiring against a key core now writes.
- [ ] Mechanical pass on the `reference.md` edit.
- [ ] Four gates. **Delta: +1 test.** Commit.

**What this task must NOT touch.** The four rows of § What `study add` redacts — the ruling adds a
**reason**, not rows. `study.py`'s code (only task 7 touches its docstring). Arm S's test bodies. § The
two files (task 2's). § Errors core raises (task 5's).

---

## Task 5: Ruling N — two § Errors rows, one per code, covering every reach path

> **Bindings that reach this task:** **Ruling N** and design Decisions 2, 3 and 4, all restated below.

**RULING N, restated here in full:** the charter widens to **TWO** of the nine undocumented codes, not
three and not nine. The scoping recommended *"take these three, leave six"*, but **H6a already gave
`E-CODE-DIRTY` its row** in its batch-4 follow-up — verified here by reading, not by the ledger:
`grep -n "E-CODE-DIRTY" docs/reference.md` returns one hit and it is a full § Errors core raises row.
So what remains is `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT`. **Take both.** Grounds: H6's surface is
hashes and provenance, and both are raised by the git layer H6a just rewrote — **a code whose emit site
this slice's own work touched is inside the charter.** The others belong to their own surfaces;
**each is filed with an owner that is a fact with a reason**, never *"whichever slice next touches X"*
— that is task 8's. **The ruling as it arrived said *"the other six"*; § Corrections 18 re-derives it
to FIVE, and task 8 uses five.** **One row per code covering EVERY emit site** — that shape was the whole-branch
Major on two sub-slices, shipped twice in a third, and miscounted twice in H5b. **And check each
table's own SCOPE SENTENCE, not this plan's instruction**: H6a's batch 4 put a row in a table whose
scope did not admit it, and its batch review settled the question by **citing the design**, which is
answering from a proxy.

**The scope check, done here so the task confirms rather than re-derives — and confirms by reading the
table, not by reading this paragraph.** § Errors core raises' header is `| Raised by | Type · code |`,
over a preamble that introduces the exception hierarchy and then says *"Two rows in this table are not
raises, and the `Type` cell says so"*, siting `E-CODE-DIRTY` and `E-CODE-EMPTY` there because
*"`validate` does not report them … a reader who meets one at `run` looks for it here."* **Both new
codes ARE raises and both carry `ContractError`**, so neither needs an invented `Type` cell and neither
widens the table's scope. **Read the preamble and the header yourself and report what they say.**

**Decision 2 — what `E-GIT-NO-REPO`'s row must carry.** One raise, in
`provenance.find_repo_root`, and **six** paths that reach it. Measured at the console script:

| Reached from | What happens |
|---|---|
| `cli.command_run` | **uncaught** — `main`'s `except PublishableError` prints it to **stderr**, exit 1 |
| the `generate`/`init` dispatch, `find_repo_root(Path.cwd())` | **uncaught**, same printer, exit 1, and the walk-up starts at the **working directory** |
| `validate._check_data` | caught by code, `return`s quietly — *"not in a repo, so inside-the-repo doesn't arise"* |
| `validate.validate_config` | caught by a **bare `except ContractError`**; `repo_root` becomes `None` and local template discovery is skipped |
| `cli._load_experiment_for` | caught by `except Exception`, returns `None` |
| `study._refuse_if_in_repo` | caught by code as the **pass branch** of `E-STUDY-IN-REPO` |

The row must carry four things: the single raise; that `run` and the creation commands **surface** it at
exit 1 on stderr; that the creation commands walk up from the **cwd**, being the commands with no path
argument to walk up from — **the one place `CLAUDE.md` § Invariants' *"a walk-up from the path the
command was given, not from the working directory"* does not apply, and a reader who compares the two
without that sentence concludes one is wrong**; and that `validate` and `study` catch it **by code** as
the pass branch of a rule of their own, which is why a config outside every repository prints
`✓ config valid` and then refuses at `run`.

**Decision 3 — what `E-GIT-NO-COMMIT`'s row must carry.** Raised by `provenance.git_provenance` on a
repository with no `HEAD`; **one** reach path, `cli.command_run`
(`grep -rn "git_provenance" src/` → the definition, one import, one call); and raised **while
computing** the `GitInfo` the dirty gate reads, so it **precedes** `E-CODE-DIRTY` — a fresh `git init`
with two untracked trees reports this code, not the gate's. Measured. The row also records why the
check exists, which is in the code's own comment: `--verify` is used because plain
`git rev-parse HEAD` writes the literal string `HEAD` to stdout as part of its usage hint on a
commitless repo, which `_git`'s `check=False`/`strip()` convention would read back as a commit.

**Decision 4 — where the rows go.** Beside **the row whose subject is `src/**` or `templates/**`
carrying uncommitted changes when a command that executes starts** — named by what it does, never by
position, never as *"the two rows above"*. **When you insert a row, check every row it moved and every
count phrase near it**: § Errors core raises' preamble says *"Two rows in this table are not raises"*,
and adding two rows that **are** raises must leave that count at two.

**Steps**

- [ ] Read § Errors core raises' preamble and column header and **report what they say** before writing
      either row.
- [ ] Write the two rows, one per code, each carrying everything Decisions 2 and 3 name.
- [ ] **Check the preamble's *"Two rows"* count is still true**, and every count phrase near the
      insertion point.
- [ ] **Fixture G — one row per code, checked mechanically.** Extract every code from § Errors core
      raises' `Type · code` column, **and independently** grep `src/publishable/` for
      `code="E-GIT-NO-REPO"` and `code="E-GIT-NO-COMMIT"`. Assert each code appears in **exactly one**
      table row and has **exactly one** raise site. **Both ends are read** — a test that compares the
      table with itself measures only that the table equals itself.
- [ ] **Run both mutations:** **9** delete `E-GIT-NO-REPO`'s row → Fixture G fails on the table side
      while the `src/` grep still finds the raise. **10** add a second row for `E-GIT-NO-COMMIT` →
      exactly-one becomes two.
- [ ] **Named blind in advance, and owed a replacement:** a mutation to either row's **prose** is
      caught by nothing — no test reads a row's sentence. The replacement is **Fixture G plus arm T**:
      G pins that the row exists exactly once and the code is raised exactly once, T pins the behaviour
      the row describes (code, stream, exit code, ordering). The residue — a row whose English is wrong
      while its code, count and behaviour are right — is the batch review's, named here rather than
      discovered there. **Report that you left it, do not report zero.**
- [ ] Run arm T and report it passes **without an edit** — this task documents behaviour and changes
      none.
- [ ] Mechanical pass on the edited file.
- [ ] Four gates. **Delta: +1 test.** Commit.

**What this task must NOT touch.** `src/` — no code, no comment. The other seven undocumented codes
(task 8 files them). `E-CODE-DIRTY`'s existing row. § Exit codes and diagnostics. Arm T.

---

## Task 6: Ruling P and Decision 12, decided together

> **Bindings that reach this task:** **Ruling P** and design Decision 12, both restated below. The
> `spec-defects.md` entry itself asks for the two to be decided together, which is why they are one
> task.

**RULING P, restated here in full:** **no new `W-` code** for § Templates' *"goes dirty at `validate`"*,
and **the sentence STAYS**. H6a's design appended a correction establishing that the sentence is **true
as written**: discovery imports every file under `templates/` to find its registration, which writes
`templates/__pycache__/`, so a repo whose `.gitignore` omits that line **becomes dirty as a result of
validating**. Grounds for adding nothing: **a `W-` code is a registry seat**, the condition is already
caught at `run` by `E-CODE-DIRTY`, and the scaffold's own `.gitignore` excludes `__pycache__` so only a
hand-assembled repo reaches it. **This task is a confirmation, not a change** — and its job is to check
the sentence against the code **as H6a left it**, since Ruling F changed what the surrounding paragraph
claims.

**What Ruling F changed, and it is the likely finding.** § Templates' neighbouring clause reads
`code_hash` *"skips `__pycache__` directories and compiled `.pyc`/`.pyo` files unconditionally,
wherever in the hashed trees they sit — it reads the working tree rather than git, so no ignore file
could have done that for it."* **The second half is now false: the hash asks git.** The fixed skip set
is still applied unconditionally, which is what keeps the first half true. **So the paragraph the
scoping did not name is where the defect probably is.** **Prefer deleting a false clause to rewriting
it.**

**Decision 12, restated in full:** `spec-defects.md` carries *"OPEN — an uncommitted root `.gitignore`
decides what `code_hash` covers, and the dirty gate cannot see it — **Owner: H6b**"*, filed 2026-08-23
by H6a's whole-branch fix round. **H6b DECLINES it, in writing, and re-owns it unassigned with the
reason.** Grounds: closing it means the dirty gate reading a file **outside** the two hashed trees —
a **behaviour change to a shipped command**, where every uncommitted root file becomes a candidate the
gate must rule on and a repo with an ordinary uncommitted `README.md` would stop running. H6b is
chartered **additive**; this is the one item in its inbox that cannot be done additively. The entry's
own owner paragraph asks a successor to decide it **together with** the `validate` tree-state ruling,
and Ruling P answers that one with *no new seat*; answering this one with *widen the gate* would leave
the two decided in opposite directions in one slice, on no argument. **A decline is recorded as an
amendment, never as a strike** — the gap is real and reproduces, and the entry's own recipe stands.

**Steps**

- [ ] **Measure, do not read.** Build a hand-assembled repo whose `.gitignore` omits `__pycache__`,
      with a `templates/` holding a real registering template. Run `git status --porcelain`, then
      `publishable validate`, then `git status --porcelain` again. **Report all three outputs.** That
      is the measurement Ruling P's confirmation rests on, and it is the difference between an
      assertion and a fact.
- [ ] Re-read **the whole § Templates paragraph** against the code at HEAD, not only the sentence the
      scoping named. Report, clause by clause, which are true and which are false. The
      *"no ignore file could have done that for it"* clause is expected to be **false**; report what
      you find, and if it is false, **delete the false clause** rather than rewriting the sentence
      around it. `grep -rn "excludesFile" src/publishable/hashes.py src/publishable/provenance.py` is
      the check.
- [ ] **Add nothing to any registry.** No `W-` code, no § Warnings row, no § Validation row. If your
      measurement contradicts Ruling P — if `validate` genuinely does not leave the tree dirty — **stop
      and report it**; that is a controller question, not a task's licence to mint a seat.
- [ ] Amend the OPEN root-`.gitignore` entry in `spec-defects.md`: H6b considered it, **declined** it
      on the additive-charter ground above, decided it beside Ruling P as the entry asked, and re-owns
      it **unassigned, with the reason** — no remaining chartered slice has `E-CODE-DIRTY`'s pathspec
      as its surface (H9 is `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`; H3c-3's remaining 14
      are folds and holdouts inside cells) — and name the closer's own cost accounting: what an
      uncommitted root file that is **not** a `.gitignore` should do at the gate. **Amend, never
      strike.** A struck entry reads as closed.
- [ ] Amend the entry that names *"H6b task 18's ruling"* about whether `validate` gains a tree-state
      seat, recording Ruling P's answer: **no seat**, with the three grounds.
- [ ] Mechanical pass on every `*.md` you edited.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** `src/`. `tests/`. Any registry — no new code of any kind.
§ How the three are computed, which H6a wrote and which is not this task's to re-litigate. The other
`spec-defects.md` entries (task 8's).

---

## Task 7: the three stale claims — one deleted, one rewritten, one deleted

> **Bindings that reach this task:** design Decision 13. **Prefer deleting a claim to rewriting it** —
> a rewrite invents; a deletion cannot. A round that closed a false-owner comment closed it by
> **propagating the claim to two more sites**, which is why that rule is stated here rather than
> assumed.

| Where | The claim | What to do |
|---|---|---|
| `src/publishable/secrets.py` module docstring | *"`provenance.environment` is assembled from `os`, `hostname`, `hardware` and `uv.lock` alone"* | **DELETE the enumeration.** It is **false at `2b18435`** — the block is `{manager, python_version, uv_lock, uv_lock_hash}`, so it names three keys that did not exist and omits three that did — and it stays false after task 3, which adds the three and removes none of the four. The sentence's job is *"Never touches provenance"*, and the structural ground beside it — *"nothing in this module imports `publishable.provenance` or writes into the document it builds"* — carries the whole claim on its own |
| `src/publishable/study.py::_redact` docstring | `hostname` *"is never written today (measured at `ebf642a`: `provenance.environment` is `{manager, python_version, uv_lock, uv_lock_hash}`) — it is H6's … becomes 'redacted' the day H6 writes it, with no code change here"* | **REWRITE to the fact**, the one exception the rule allows: the sentence's subject *is* the arrival of this slice. The day arrived, no code changed here, and Fixture E is the pin. Keep the dated `ebf642a` measurement and mark it superseded rather than deleting the history |
| `tests/test_study.py::_fixture_y_record` docstring | the same `ebf642a` parenthetical, plus *"which nothing in this build writes"* | **DELETE the parenthetical.** The fixture's own reason for existing — a hand-built record exercising every redacted field at once — survives unchanged, and it stays valuable **beside** Fixture E rather than replaced by it. This is a **docstring** edit to a test named as guard-pin arm S, authorized here and nowhere else; **no assertion and no value in `_fixture_y_record` moves** |

**Steps**

- [ ] Make the three edits.
- [ ] **Sweep for the claim, not for the file the claim was first noticed in.** Three sweeps in one
      slice stopped one file short. Grep — newline-insensitively, over `src/`, `tests/`, the four
      documents **named individually**, `CLAUDE.md`, and `docs/superpowers/spec-defects.md` — for
      `never written`, `ebf642a`, and `manager, python_version` (whitespace-flattened). **Report every
      hit and what you did about it.** A tracked record (`docs/superpowers/**`,
      `.superpowers/sdd/**`) is **appended to, never retro-edited** — a spec records what was decided
      when it was written, and `spec-defects.md` is the one live list.
- [ ] Run arm S and report both tests pass. The docstring edit moves no assertion; report the
      `git diff` line count.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** Any assertion in `tests/test_study.py`. `study.py`'s or
`secrets.py`'s **code**. The other stale-claim candidates a sweep may turn up in a tracked record —
report them, do not retro-edit them.

---

## Task 8: `spec-defects.md` — one entry closed, the rest filed with owners that are facts

> **Bindings that reach this task:** **Ruling N**'s filing half, restated below, and design Decision
> 14. **A ledger line saying "filed" is not a filing** — a gap recorded as *"registered against
> \<owner\>"* once existed only in a ledger while the defects file had no such entry. **An entry naming
> its owner as *"whichever slice does X"* points at a closed slice once X lands.**

**RULING N's filing half, restated:** H6b takes `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT`. **The others
belong to their own surfaces; file each with an owner that is a fact with a reason**, never *"whichever
slice next touches X"*.

**THE COUNT IS FIVE, NOT SIX, AND YOU MUST NOT CARRY EITHER NUMBER WITHOUT RE-DERIVING IT.** The ruling
as it arrived said *"the other six"*. That subtracted `E-CODE-DIRTY` from the nine and **not**
`E-EXPERIMENT-UNKNOWN`, which H8c task 16 documented (`c794029`, recorded in the entry's own appended
note). Derived: the nine are `E-GIT-NO-REPO`, `E-GIT-NO-COMMIT`, `E-CODE-DIRTY`, `E-INPUT-CHANGED`,
`E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`,
`E-EXPERIMENT-UNKNOWN`; minus the two already documented leaves **seven**; minus H6b's two leaves
**five**. **`E-STEP-EXISTS` is NOT one of the nine** — the entry names it as *"the one sibling that is
documented, and only partially"* — so it is recorded as a separate observation and never counted in.
**Re-derive this yourself from the entry's table before writing the number**, and report the
derivation; a count carried forward without re-deriving what it counted is the failure this repo has
made twice, and this plan's own first draft made it a third time.

**Steps**

- [ ] **Close the six-unwritten-keys entry** — *"Six `provenance` and `results` keys in the `run.yaml`
      example that no code writes"* — **only after checking every row of its own table.** Its
      `provenance.allocation`/`.allocation_hash` row was struck at H3c1 task 14, `provenance.upstream`
      at H8a task 7, and `provenance.environment.os`/`.hostname`/`.hardware` is closed by task 3.
      **Verify each of the two prior strikes against the code at HEAD** rather than trusting the
      amendments; a filing's claims about the code go stale like any other comment. The entry's own
      *"Also recorded, and deliberately not fixed"* key-order note about `provenance`'s construction
      order **stays** — H6b added no top-level key and reordered nothing — and say why it stays, so a
      later reader does not read the closure as covering it. Record that `environment` is now the one
      sub-block whose key order matches the example exactly, and that this was matching a document
      rather than reordering an example.
- [ ] **Append to the nine-undocumented-codes entry**, correcting the count: H6a took one
      (`E-CODE-DIRTY`), H8c had already documented `E-EXPERIMENT-UNKNOWN`, and **H6b takes two**
      (`E-GIT-NO-REPO`, `E-GIT-NO-COMMIT`). **Verify each claim by reading `docs/reference.md`, not by
      reading the entry's own amendments** — H6a's batch 6 found that both its brief and its design
      said H6a *"took none"* when it had taken one, found by `git log -S` rather than by reading. State
      the remaining count and enumerate what remains: `E-INPUT-CHANGED`, `E-RUN-LOCKED`,
      `E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS` and `E-EXPERIMENT-EXISTS` — **five, derived above and
      not carried**, and the heading's count goes from nine to five. **Owner: unassigned, with the
      reason** — no remaining chartered slice has `run_identity.py`, the manifest path or `generators/`
      as its surface: H9 is `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`, H3c-3's remaining 14
      are folds and holdouts inside cells. **And re-verify the entry's own "a mention inside another
      code's row is not documentation of that code" states** for each of the five, by sweeping the four
      documents **named individually** — that distinction is the entry's heading, and it went stale for
      one row before.
- [ ] **File: `validate_config`'s bare `except ContractError` around `find_repo_root` is wider than its
      comment's claim** (*"No repo at all"*). It would swallow any future coded fault from the walk-up.
      Reproduce: read the two catch sites and note that `_check_data`'s neighbour catches **by code**
      while this one does not. Narrowing it is a behaviour change to `validate`, so it is not H6b's.
      **Owner: unassigned, with the reason** — no remaining chartered slice has `validate`'s
      template-discovery path as its surface.
- [ ] **Record `E-STEP-EXISTS` as a separate observation, NOT as one of the nine.** It has a sentence
      in § Exit codes and diagnostics and no § Errors row, and the entry already calls it *"the one
      sibling that is documented, and only partially."* Counting it in is what turned five into six in
      this plan's own first draft; label it as what it is, beside the five.
- [ ] **Record as a stated non-gap, not as a filing:** `diff` gains no row for `os`/`hardware`
      (Decision 14). § What `diff` compares says *five rows* and the five-row shape is documented and
      deliberate, so no owner is invented for it. Say this **once**, in the six-unwritten-keys closure,
      so a later reader does not file it as a gap.
- [ ] **Every sweep names its files, filters the file list rather than the output, is
      newline-insensitive, and is proven able to fail** against a control string known to be present.
      This is a rule about the checker as much as the claim: H6a's batch 6 disclosed that its own
      mechanical checker produced eight false positives on first run.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** The two entries task 6 amends — the root-`.gitignore` one and the
`validate`-seat one. Any tracked record other than `spec-defects.md`, which is the one live list; a
spec or a scoping is **appended** to, never retro-edited. § Executability (task 11's). `src/`, `tests/`.

---

## Task 9: `CLAUDE.md` — the slice entry and the order line

> **Bindings that reach this task:** **Rulings N, O, P, Q** all reach the slice entry, which must state
> what H6b did and did not do. **§ Executability does not move** (design Decision 15) and the entry must
> say so **without quoting a single number for this analysis' executability** — quote the table or name
> the dependency.

**Steps**

- [ ] Update the order line. It reads *"Order of the slices that remain: H6b, H9, then H3c-3's
      remaining 14"*; it becomes **H9, then H3c-3's remaining 14**. Check every sentence near it that
      counts slices or names H6 — **when you remove a string, grep `CLAUDE.md`, the four documents
      named individually, and any feasibility analysis for what should no longer exist.**
- [ ] Add the slice entry, in the running record's own voice, stating: the three keys written; **zero
      refusals retired and ZERO configs unblocked**; Ruling O's trade — a GPU is an apparatus fact and
      the example lost it, so a bundle reader cannot tell what hardware produced a number unless the
      producer declared a probe; Ruling Q's reason, and that **the pin is the point** because H8c wrote
      the redaction against a key nobody wrote; Ruling N's two rows and the **five** that stay filed,
      with the heading's count corrected from nine and the derivation given; Ruling P's *no seat*; and Decision 12's **decline** of the
      root-`.gitignore` filing, with the reason — a slice chartered additive cannot widen a shipped
      gate's pathspec.
- [ ] **Say § Executability does not move, and do not quote a number.** Either point at the table or
      name the dependency: `io.reuse_from`'s plugin-side call for six, the `report_by`-under-`resample`
      gap for seven, and 8 of 8 validating clean, which is the only figure `validate` can see.
- [ ] Three or four things worth carrying, in the running record's shape. Candidates, and the report
      should say which it chose and why: **the charter was stale in the same direction again** — three
      of eight rows, and one whole task the scoping could not contain because H6a's own gate filed it
      afterwards; **a pin that must move was moved once, by a named editor, with the post-edit state
      written in the shape the design had already decided** — the answer to H6a's batch-2 Major;
      **the sibling that already got it right** — `run_identity` already answered *what machine is
      this*, so `hostname` needed no new call; **a fixture that recomputes the implementation cannot
      fail**, which is why `os` is pinned with installed sentinels rather than with the composition
      itself; and **a false enumeration was deleted rather than rewritten**, in a docstring whose
      structural ground already carried the claim.
- [ ] Mechanical pass on `CLAUDE.md`.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** The four documents. `docs/feasibility-llm-growth-studies.md` (task
11's). Any number in the four-row table.

---

## Task 10: the consistency passes

> **Bindings that reach this task:** `CLAUDE.md` § Checking consistency after any `*.md` edit. **Both
> passes govern the four documents only — never the development record.** A feasibility analysis is
> **exempt** from the cross-document pass and subject to the mechanical pass in full.

**Steps**

- [ ] **Mechanical**, over every `*.md` this branch edited, written as throwaway greps or a short
      script rather than a kept checker: every relative link and `#anchor` resolves; no two headings in
      a file produce the same anchor; every table's rows match its header's column count and no row is
      empty; no line carries trailing whitespace, a tab, or invisible unicode. **Skip fenced code
      blocks in all of it** — the docs contain markdown inside markdown, and a `##` or `|` there is
      content. **Debug the checker before trusting it**: H6a's batch 6 disclosed eight false positives
      on its first run, the third time in two slices a sweep could not be trusted until debugged.
- [ ] **Cross-document**, over the four documents named individually, against `CLAUDE.md`'s own table
      of the classes that drift. The two that this branch can plausibly have broken:
      **Schema fields in prose** — `os`, `hostname` and `hardware` are named in prose and must exist in
      the `run.yaml` example, and vice versa; and **the shared worked example** — Ruling O edited a line
      inside `cohort-pilot`'s own `run.yaml` block, so check that no value the worked example carries
      moved, and that `apparatus: null` and its *"no probe declared"* comment stand. **Enum comments**
      is the third to check: `hardware`'s inline comment must not enumerate a key core does not write.
- [ ] **Sweep for what should no longer exist:** `gpu`, `A100`, and the deleted `secrets.py`
      enumeration's phrasing. **Name the files**, filter the file list rather than the output, flatten
      whitespace before matching, and **prove each sweep can fail** with a control.
- [ ] Report every finding and every fix. **A batch with no review is where the findings will be** —
      this task's output is nobody else's input, so nothing else will find its errors.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** The development record — `docs/superpowers/**` and
`.superpowers/sdd/**` are appended to, never retro-edited, and `spec-defects.md` is the one exception
and is tasks 6 and 8's. `src/`, `tests/`. § Executability (task 11's).

---

## Task 11: § Executability — one dated entry, four rows character for character, no fifth number

> **Bindings that reach this task:** design Decision 15. **Derive whether the table moves; do not
> assume it.** Both of the wrong figures this analysis has carried were made by a slice that retired a
> blocker, moved configs out of a column, and **carried the summary phrase forward without re-deriving
> what it counted.**

**Steps**

- [ ] Append one entry to `docs/feasibility-llm-growth-studies.md` § Executability, headed
      *"Measured on 2026-08-23 against commit \<sha\>"* — the sha of this branch's tip at this task.
      **Also state which executable tree that sha names**: run
      `git diff --name-only <last src/tests commit>..HEAD -- src tests` and report it, so a reader can
      see that the measurements describe the tree the sha carries. On H6a's and H5b's precedent.
- [ ] **Write the derivation ahead of the table**, so a reader checks the reasoning rather than
      checking that the characters match:
      **Row 1 counts configs validating with zero *errors*.** H6b emits nothing at `validate` —
      it writes three keys inside `cli.command_run`, documents two codes raised by `provenance.py`, and
      edits documents. **Documenting a code changes no behaviour.** Confirm by sweep:
      `grep -c "E-GIT-NO-REPO\|E-GIT-NO-COMMIT" src/publishable/validate.py` → **1**, and that one hit
      is the **catch** at `_check_data` that makes the check pass quietly, not an emit — read it and say
      so. Control: `grep -c "E-PARAM-MISSING" src/publishable/validate.py` → **3**, so the sweep can
      find a code `validate` does report.
      **Rows 2 and 3 name dependencies H6b does not touch** — `io.reuse_from`'s plugin-side call, and
      the `report_by`-under-`resample` construction inside `summarize_step`.
      **Row 4 counts configs free of every core-side dependency this analysis can name.**
      `provenance.environment` is written for every run regardless of config; no declaration opts in
      and none opts out, **so no config gains or loses a dependency**.
      **Neither documented code can fire for any of the nine** — both are properties of a
      **repository** (none at all, or one with no commit) and neither reads any declaration.
- [ ] **Copy the four-row table out of the analysis' own immediately preceding entry with `sed`** and
      `diff` your extraction against it. **Do not retype it and do not copy it from this plan's
      opening** — a second source of truth is how both wrong figures were made. Report that the diff is
      empty.
- [ ] **No fifth number, and no single figure quoted for this analysis' executability.** Quote the
      table, or name the dependency.
- [ ] **State what newly stops and what newly warns, in prose and separately from the table:**
      **nothing.** H6b mints no code and retires none; the two it documents were already raised. Say it
      as a derived claim with the sweep above behind it, not as a reassurance.
- [ ] Mechanical pass on the edited file — the analysis is **exempt from the cross-document pass** and
      subject to the mechanical one in full, including `×` for multiplication and hyphens in anchors.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** Any earlier § Executability entry — the section is append-only.
The four documents. `CLAUDE.md`. `src/`, `tests/`.

---

## Corrections against the code

Appended by this plan's author, extended by no task. Each was grepped or run at `2b18435`. **Reported
as a list, never as a count of zero.**

1. **The scoping's task 17 asks for `E-CODE-DIRTY`'s row and it already exists.**
   `grep -n "E-CODE-DIRTY" docs/reference.md` → one hit, a full § Errors core raises row with a
   `Type` cell reading *(no exception; a `Collector` diagnostic)*. Ruling N is built on this.
2. **The scoping's task 18 frames a change; H6a's design appends a correction saying the sentence is
   true.** Read the design's § Correction, 2026-08-23. Ruling P follows it.
3. **H6b owns a filing the scoping cannot contain, because it was written afterwards.**
   `grep -n "H6b" docs/superpowers/spec-defects.md` → the OPEN root-`.gitignore` entry, **Owner:
   H6b**, filed 2026-08-23 by H6a's whole-branch fix round. It is Decision 12 and task 6.
4. **The scoping's three tasks 13/14/15 cannot be three tasks.** They write one dict literal and each
   invalidates the same shipped assertion,
   `tests/test_cli.py::test_h8b_arm_d_the_five_figures_diff_reads`'s
   `assert environment == {"manager": "uv", "uv_lock": None, "uv_lock_hash": None}`. One task.
5. **`cli.py` imports none of `os`, `platform` or `socket`.** Grepped for `\bos\.`, `\bplatform\.`,
   `\bsocket\.` and `import os\b`: **zero hits**. Task 3 adds three imports, which the scoping's rows
   (*"`platform` is stdlib"*, *"`cpu_count` is stdlib"*) imply and do not state.
6. **`hostname` already has a source in this codebase.** `run_identity.py` writes
   `socket.gethostname()` into the run lock. The scoping does not name it, and *the sibling that
   already got it right is the first place to look.*
7. **`os.sched_getaffinity` does not exist on the platform this plan was written on** (measured), so it
   cannot be `cpu_count`'s source even as a preference. The scoping says only *"`cpu_count` is
   stdlib"*.
8. **`platform.platform()` reports a different fact from `uname`.** Measured:
   `'macOS-26.5.2-arm64-arm-64bit-Mach-O'` against `Darwin`/`25.5.0`/`arm64`. The scoping does not
   name a source for `os` at all, and the obvious one-call answer is the wrong one.
9. **Three shipped claims about the environment block go stale or are already false, and the scoping
   names none.** `secrets.py`'s docstring enumeration is **false at `2b18435`**;
   `study.py::_redact`'s and `tests/test_study.py::_fixture_y_record`'s `ebf642a` measurements go
   false at task 3. Task 7.
10. **Only two readers of `provenance.environment` exist and neither iterates it.** Grepped for
    `"environment"`, `["environment"]` and `environment.get` over `src/publishable/*.py`:
    `diff._figure` reads `uv_lock_hash`, `study._redact` reads `hostname`. Every other hit is the
    **directory** `environment/`. This is what makes the slice additive, and the scoping asserts
    additivity without measuring it.
11. **No hash reads the record.** `grep -n "hash(provenance\|hash(run_doc\|hash(record"
    src/publishable/*.py` → nothing, and the `provenance` mapping is built after `hashed_files`,
    `code_hash_of`, `parameters_hash`, `design_digest`, `manifest_hash`, `units_hash` and
    `allocation_hash` have all run. Stated because *the additive claim is the framing of this whole
    slice* and a framing is a claim too.
12. **`E-GIT-NO-REPO` has one raise and six reach paths, three of which swallow it deliberately.** The
    scoping calls it *"`provenance.py`, the walk-up this slice is named for"* and stops there. The
    creation commands' walk-up is from the **working directory**, which is the one place
    `CLAUDE.md` § Invariants' walk-up rule does not apply; a row that omits it invites a reader to
    conclude the invariant is broken.
13. **`E-GIT-NO-COMMIT` precedes `E-CODE-DIRTY`**, measured: a `git init`-ed copy of a working project
    with both hashed trees untracked reported `E-GIT-NO-COMMIT`, not the gate.
14. **`validate` prints `✓ config valid` at exit 0 on a commitless repository and on no repository at
    all**, measured at the console script. Both then refuse at `run`. The scoping's § 6 table covers
    the dirty and ignored cases and neither of these.
15. **No existing test asserts either code through `main([...])`.** Grepped newline-insensitively over
    every file in `tests/`: nine hits, two direct calls, four monkeypatched raises, two docstrings, one
    comment — none through the CLI. Arm T is new coverage, and this is reported as a grep rather than
    as a claim, because *brief-supplied prose is where zero hides*.
16. **`_H5A_ARM_D_LITERALS` contains nothing on the `hardware` line**, so Ruling O's edit cannot move
    an arm with no authorized editor. Checked by extracting the tuple and testing each member against
    the literal line, not by reading the tuple.
17. **`study new` refuses a bundle inside a git repository**, so Fixture E's bundle must live under
    `tmp_path` outside the project. Read at `study._refuse_if_in_repo`, whose pass branch is
    `E-GIT-NO-REPO` — the same code task 5 documents, reached from a third direction.

18. **The controller ruling's *"the other six"* is FIVE, re-derived from the entry's own table.** Nine
    minus `E-CODE-DIRTY` (H6a batch 4) minus `E-EXPERIMENT-UNKNOWN` (H8c task 16, `c794029`) is seven
    undocumented before H6b; minus H6b's two is **five**: `E-INPUT-CHANGED`, `E-RUN-LOCKED`,
    `E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`. This plan's and the design's first
    drafts both said six and both filled the sixth slot with **`E-STEP-EXISTS`, which was never one of
    the nine.** Corrected in both before dispatch. Reported here rather than silently fixed, because
    **a disagreement with the authority that commissioned the work is exactly the kind this repo asks
    to be surfaced**, and because task 8 writes the number into a live filing.
19. **Thirteen other tests read `docs/reference.md` as text, and none extracts § The two files'
    `run.yaml` block.** Seven sites in `tests/test_cli.py`, five in `tests/test_diff.py`, one in
    `tests/test_report.py`. Swept for every literal of the environment block (`hardware`, `A100`,
    `hms-gpu-node`, `Linux-6.8.0`, `manager: uv`, `python_version:`, `uv_lock:`, `environment:`,
    `The two files`), control `grep -c "uv_lock_hash" tests/test_cli.py` → **4**. The only `A100` hits
    are `tests/test_report.py`'s **apparatus** fixture facts, which are correct and which task 2 must
    not move. **So arm R is the only pin task 2's edit can reach, and no additional post-edit state is
    owed.** Measured because the alternative — one checked pin and thirteen unchecked — is how H6a's
    batch-2 Major happened.

---

## Live overrulings — restated here because a ruling that overrules a brief has to reach the brief

**The ledger reaches the controller and the reviewers; it reaches no implementer.** Each of these is
restated inside the task section it binds, above, and is repeated here so a controller assembling a
dispatch can see the whole set.

1. **The scoping's three-code recommendation is overruled to two** (Ruling N). Restated in task 5 and
   task 8.
2. **The scoping's task-18 framing is overruled to a confirmation** (Ruling P). Restated in task 6.
3. **The scoping's three-task split of the environment keys is overruled to one task** (§ Corrections
   4). Restated in task 3 and in § Sequencing.
4. **`gpu` leaves § The two files' example** (Ruling O), rather than being sourced from the apparatus
   inside it. Restated in task 2, with the measurement that decided it.
5. **The root-`.gitignore` filing is declined, not closed** (Decision 12), and amended rather than
   struck. Restated in task 6.

---

## What could not be measured

- **`os.cpu_count()` returning `None` was never observed**, only documented. Fixture C arm 2 installs
  it by monkeypatch, which measures the code's handling and not the platform's behaviour.
- **The `os` string on Linux and Windows was not observed.** Fixture A's sentinels make the test
  independent of the platform either way, which is the reason for the sentinels beyond
  discrimination.
- **The uncommitted-root-`.gitignore` gap was not re-perturbed.** Decision 12 declines it and relies on
  H6a's 2026-08-23 measurement, whose reproduction recipe is in the entry. A decline needs no
  re-measurement; a strike would have.
- **Whether `W-PARAM-UNSET` fires on the feasibility analysis' nine configs is still unknowable**, for
  the reason every entry since H7b's has recorded: neither `growth_screen` nor `publishable-llm` is
  installable in any build. Task 11 must not resolve it; the H6a entry's *unknowable with a reason* is
  the honest form and stands.

---

## Plan self-review

- **Every binding ruling is restated inside the task section it binds**, in full rather than by
  reference, because `task-brief` extracts one section and nothing else — which is how a slice shipped
  a Critical two slices ago. Rulings N (task 5, task 8), O (tasks 1, 2, 3), P (task 6), Q (tasks 3, 4).
  Ruling O appears in **task 1** as well as task 2 and 3, because it decides arm P's advance spec and
  arm P is captured before either.
- **Each task states what it must NOT touch**, and every arm with no authorized editor is named as
  run-only in every task that could reach it.
- **Every mutation has two branches checked in advance to be able to differ**, and the two blind ones
  are named in advance with replacements — Fixture G plus arm T for the § Errors prose, and the batch-5
  review for the records.
- **The guard pin is captured in task 1, in the shape Ruling O decided**, with five of six arms having
  no authorized editor and arm P's post-edit state written before anything moves.
- **The four-row table appears in this plan's opening and is explicitly disowned as a source of
  truth**; task 11 extracts it from the analysis with `sed` and diffs.
- **No task reports a count of zero disagreements**; every claim about other tests or rows is a grep the
  task must run and report.
