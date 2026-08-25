# H9d batch review — reviewer for every batch, verdicts per task

**Reviewed at `7f441a9`** (25 commits ahead of `main`). Suite re-run by me, foreground, unfiltered:
**3338 passed, 1 skipped, 2 xfailed in 368s**. `ruff check` clean, `ruff format --check` — 101 files
already formatted, `mypy` — no issues in 56 source files. `main` is 3230, so **+108 collected**;
accounted for below.

**Method note.** Everything marked *behaviour* below was established by running the installed console
script `/Users/joon/src/tries/publishable/.venv/bin/publishable` in a scratch `HOME` **outside this
repository**, or by a mutation whose failure output is quoted. Everything marked *reading* was not.
Every mutation was reverted **by copying the backup back** and each revert verified by **re-running**
the tests it broke — never by `git status`.

---

## Test delta against `main`, with its nouns

| Where | Test functions added |
|---|---|
| `tests/test_demo.py` (new) | 20 |
| `tests/test_docs.py` (new) | 46 |
| `tests/test_sourceimport.py` (new) | 5 |
| `tests/test_cli.py` | 3 |
| `tests/test_scaffold.py` | 8 |
| Removed, net, anywhere in `tests/` | 0 (`git diff main...HEAD -- tests/ \| grep -c '^-def test_'` → 0) |

82 functions → 108 collected items with parametrization. The three `…_defers…` tests deleted by task
13 were added on this branch, so they do not appear in the `main...HEAD` diff at all — checked at
`cbfda10` itself instead (below).

---

## Per-task verdicts

### Task 1 — the guard pin — **PASS (behaviour)**

Arms C, D, F built; A, B, E, G cited rather than re-captured. All green at HEAD, and **all proven
still able to fail** by me, not by citation:

```
# mutations, then `uv run pytest tests/test_cli.py -k "h5a_arm_d or h9d_arm_c"`
README.md            sha256:6b1f -> sha256:6b2f
design-principles.md sha256:3d8a -> sha256:3d9a
reference.md         parameters_hash: sha256:1a2b... -> 1a2c...
experimental-designs.md  one appended newline
→ 5 failed, 543 deselected
  [README] [DESIGN_PRINCIPLES] [REFERENCE] and both arm-C parametrizations
# reverted by cp from backups; re-ran → 5 passed
```

Arms E and G green (`tests/test_diff.py -k h8c_arm_d` → 3 passed;
`tests/test_validate.py -k not_narrowed_by_the_null_test` → 1 passed), arm D in
`tests/test_scaffold.py` → 1 passed.

### Tasks 2–8 — the region parser, the four region bodies, `docs`, `list-templates` — **PASS (behaviour)**

**`docs` does not destroy hand-written prose, and the negative control is paired with a positive
one** — the check the dispatch flags as the one that looks identical when it silently does nothing:

```
publishable new myproj                        # outside this repo
# add HANDWRITTEN-A above ## Setup and HANDWRITTEN-B at EOF
publishable docs
  → README.md: rewrote `overview`, `credentials`, `experiments`, `templates`   exit 0
  → diff vs. pre-run copy: EMPTY (not one byte moved)
# POSITIVE CONTROL: corrupt a region body, then
publishable docs
  → diff vs. pre-run copy: EMPTY again — the body was RESTORED and the prose is intact
```

**Every refusal is named, at exit 1, and leaves the file alone** (all five reached by behaviour):

| Case built | Printed | Exit |
|---|---|---|
| `end overview` deleted | `E-DOCS-REGION-UNBALANCED` … `region credentials opens while overview (line 3) is still open` | 1 |
| `overview` opened twice | `E-DOCS-REGION-DUPLICATE` … `opened twice in one file` | 1 |
| region renamed `frobnicate` | `E-DOCS-REGION-UNKNOWN` … `is not a region core manages` | 1 |
| README with no region at all | `E-DOCS-NO-REGIONS` … file **unchanged** after the refusal | 1 |
| README deleted | `E-DOCS-NO-README`, path column names the **directory** | 1 |
| `templates` region removed | named on **stdout**, `rewrote overview, credentials, experiments` | 0 |

`E-DOCS-REGION-UNKNOWN`'s **second** sense is honestly documented: the § Errors row says it is reached
from `body_of` and `rewrite` and that *"`docs`' own top-level pass never raises the second"*. Confirmed
by reading `refresh`, which skips an absent name before `rewrite` is called, and by behaviour —
`generate experiment` into a README with no `experiments` region prints a **note** at exit `0`.

`list-templates` outside any repository prints its named absence and still lists core's and every
installed claim, exit `0` (behaviour). Its no-import claim is pinned by a **sentinel module that
records its own import**, not by an absence of output, and its ordering fixture puts a decoy on
**each** side (`aaa_probe` / `zzz_probe`) with the installed claim between — three candidate orderings
distinguished, which is the shape CLAUDE.md asks for.

### Task 9 — force recompilation at all three import sites — **PASS (mutation)**

```
# src/publishable/sourceimport.py: FreshSourceFileLoader.get_code delegates to
# SourceFileLoader.get_code (i.e. back to __pycache__)
uv run pytest tests/test_sourceimport.py tests/test_report.py
→ 3 failed:
  test_discover_local_serves_the_second_write_not_the_first
  test_render_with_override_serves_the_second_write_not_the_first
  test_load_experiment_serves_the_second_write_not_the_first
# reverted; re-ran → 5 passed
```

All three call sites are separately pinned. `import_module_fresh`'s failure shape
(`ModuleNotFoundError` with `.name`), its `sys.modules` purge-on-exception, and its pass-through for
namespace/extension specs read correctly.

### Tasks 10–11 — `demo`'s six stops — **PASS (behaviour)**

Run end to end through the installed console script, in a scratch `HOME`, outside this repo:
**129 lines, exit 0**. Under a pty: `q` at stop 2 prints all three remaining commands and the
pick-up-where-you-left-off line; re-invoking prints `Resuming the demo in … at stop 2` and continues.
`[Enter] to run it · q to stop here` is printed verbatim as README shows it, and only when stdin is a
tty (`_pause`'s `isatty` branch) — so the unattended transcript legitimately omits it.

**`demo`'s numbers are reproducible.** Two independent invocations in two scratch homes, output
normalized for `$HOME` and run id: **the only diff is the two `no uv.lock found at <cwd>/…` lines**,
i.e. the cwd. Every printed quantity — `0.697 [0.630, 0.757]`, `0.666 [0.582, 0.739]`,
`0.482 [0.413, 0.550]`, `-0.031 [-0.068, -0.002]`, `-0.215 [-0.240, -0.190]`, `228 of 240`,
`std 0.003` — is bit-stable across runs. I did not re-derive the batch's 6.2e-05 boundary margin or
its 3.66e-06 rank-neighbour gap; two whole-pipeline invocations agreeing on every digit is the
stronger check for *quoting them in README*, and correction 32's concern (a rank swap, not a rounding
swap) is what a second real run would expose.

**`demo`'s own claim about the dirty gate is true (behaviour):** appending a line to
`templates/correlation.py` in the demo project and running `run` gives
`error E-CODE-DIRTY  src/** or templates/** — uncommitted changes; commit them first`.

### Task 12 — README's transcript — **PASS with one Minor**

**README's transcript is what `demo` prints**, checked line by line against my own 129-line capture:
the stop-1 block (including the `template  templates/correlation.py` line), stop 3's
`✓ config valid · configs/correlation-pilot/config.yaml` and its whole commentary paragraph, and the
stop-5 block from the warning through the six-member correction-family paragraph, are **verbatim**.
One deviation — Minor 1 below.

**Arm B's procedural re-scan (design § 8.1) redone by me**, with the *unmodified* helper and the
*unmodified* 25-entry literal list read out of `tests/test_cli.py` at HEAD (the diff confirms neither
moved — only a comment was added above the golden):

```
literals: 25   pre(main): 15   post(HEAD): 11
post == shipped golden                  → True
removed count                           → 4   (the three table rows and the spread line)
lines appearing in post but not in pre  → []
post == tuple(l for l in pre if l not in removed) → True
```

Exactly the four named entries left, nothing else survived, nothing new appeared. Design § 8.1 step
4's finding condition did not fire, independently confirmed.

`docs/design-principles.md` and `docs/experimental-designs.md` are **byte-identical to `main`**
(`git diff main...HEAD -- <both>` empty), so `cohort-pilot`'s numbers did not move.

### Task 13 — the `NOT BUILT` retirement and `E-GIT-NO-REPO` — **PASS**

**All three `…_defers…` pairs went together**, checked at `cbfda10` itself rather than in the
branch diff: that commit deletes `test_demo_defers_to_the_unbuilt_diagnostic_while_its_row_says_so`,
`test_while_the_document_still_says_not_built_a_wrong_arity_docs_defers_to_it` and
`test_while_the_document_still_says_not_built_a_wrong_arity_list_templates_defers`, **and** the three
transitional `_report_not_built` branches in `cli.py`, **and** the three `NOT BUILT` rows. No
`…_defers…` test about these three remains in the tree (the two surviving `_defers` hits are
`test_reproduce.py`'s and `test_validate.py`'s, unrelated).

**Nothing passes vacuously as a result.** The dead
`if status == "NOT BUILT"` branch is disclosed in
`test_the_not_built_machinery_is_retained_with_no_row_marked`, which calls `_report_not_built`
directly, asserts the **exact** stderr string **and** `EXIT_INVOCATION`, **and** asserts the cited
§ heading is one `reference.md` really carries. `NOT_BUILT_COMMANDS == {}` is asserted from both ends
and every `Status` cell in `reference.md` reads `built` (52 rows mention `built`, **0** say
`NOT BUILT`).

**`E-GIT-NO-REPO` enumerated by me, by reading, then confirmed by grep.** I read every
`find_repo_root` call site in `src/` and classified each by its enclosing `try`:

| Site | Kind |
|---|---|
| `cli._prepare_run` (2514) · `cli._dispatch_generate` (5920) | uncaught — 2 |
| `validate._check_data` (1221) · `study._refuse_if_in_repo` (54) · `reproduce` config form (1391) · `docs.command_docs` (722) | by code — 4 |
| `reproduce.prepare_checkout` (373) · `validate.validate_config` (511) · `cli._preloaded_experiment` (248) · `cli.command_list_templates` (5589) | by type — 4 |

**Ten, and `provenance.py:171` is correctly excluded**: `git_provenance` has exactly one caller,
`cli.py:2521`, seven lines after `_prepare_run`'s own call, so it is not a separate path
(`grep -rn git_provenance src/` → that one call site). The § Errors row states **the breakdown**, not
a total — *"two uncaught, four caught by code, four caught by type"* — and names the three that walk
from `Path.cwd()`. My enumeration and the row agree exactly.

### Task 14 — the documents — **PASS on the mechanical and cross-document passes, HOLD on two claims**

**Mechanical pass, run by me** over the four documents named individually plus the feasibility
analysis plus `CLAUDE.md`, fenced blocks skipped: every relative link and `#anchor` resolves, no
duplicate anchors, **0** problems; a separate table pass checking each row's cell count against its
header (and for empty rows) → **0** problems; no trailing whitespace, tab, or invisible unicode → **0**.
Can-fail control: an invented anchor is reported, and the anchor sets are non-empty
(`README 15, design-principles 11, experimental-designs 24, reference 85, feasibility 54, CLAUDE 17`).

**§ Executability re-derived.** Twelve `| Figure | Count | Visible to` blocks exist; **the last eleven
are byte-identical** and only the first (pre-H8a) differs, with the two differing rows being exactly
the ones H8a rewrote. **No fifth number**, and no single figure is quoted. Row 1's `8 of 8` is
consistent with what I measured: `grep -n validate_config src/publishable/{docs,demo}.py` → no hits.

**The development record was not retro-edited**: all three touched records are **pure appends** —
`--numstat` reports `15 0`, `25 0`, `32 0` and `grep -c '^-[^-]'` is `0` for each.

**§ Package layout checked row by row against the real tree**, mechanically: every `.py` in the doc
exists, and every `.py` under `src/publishable/` is in the doc (the three that looked missing —
`experiment.py`, `step.py`, `template.py` — are under the `generators/` row, which names them).
`readme_templates/`, `docs.py`, `demo.py`, `sourceimport.py` all present. No `— not yet built` marker
survives, and the sentence carrying it is the self-maintaining one.

**The scaffold change is confined to the README, verified against `main`'s own binary.** I built a
`main` worktree, `uv sync`'d it, ran `publishable new myproj` from each build and diffed:
`diff -rq --exclude=.git` reports **exactly one file differing — `README.md`**. And the direction is
document→code: `main`'s `reference.md` **already** documented `overview`/`credentials`/`experiments`
while the code wrote only `overview`, so this closes a doc-vs-code gap rather than opening one.

`.demo-progress` and `~/publishable-demo-data/` are both documented in `reference.md`.

### Fix round 2 — **both claims verified (behaviour)**

- **Three `E-DEMO-*` identifiers retired.** `grep -rn E-DEMO src/ docs/ README.md tests/` → **one**
  hit, `tests/test_demo.py:442: assert "E-DEMO" not in source`. The pin exists and is a real
  assertion over the module source.
- **`demo`'s refusal moved to exit `1`.** Behaviour: `demo --into <occupied dir>` prints
  `error E-PROJECT-EXISTS` through a `Collector` and exits **1**; a wrong arity still exits **2**,
  which is the invocation code and correct. See Minor 2 for the message.
- All five `E-DOCS-*` codes have **exactly one** § Errors row each (`grep -c` per code → 1, 1, 1, 1, 1).

---

## Findings

**Major 1 — § Randomness' corrected sentence is still FALSE of the code, and both the report and the
filing claim it is true.** Ruling GG's fourth obligation was precisely *check these statements against
the code rather than assume them correct*; the constructor half was corrected and **the argument half
was not**.

`reference.md` § Randomness now reads *"Where there is no repeat that means `self.rng` is exactly
`random.Random(self.derive_seed("<this step>"))`"*. Measured:

```
uv run python -c "...S(BaseStep); s._bind(..., seed=0); print(s.rng.random())"
draw from self.rng      : 0.8444218515250481
random.Random(0)        : 0.8444218515250481      <- what the code gives
Random(derive_seed('S')): 0.3711685746385498      <- what the document claims
```

`runner.py`'s bind site is `seed = seeds[label]` for `repeat` scope and **`seed = 0` otherwise**, so
every `run`-, `condition`- and `summary`-scoped execution in **every** run shares `random.Random(0)`.
The other reading of "no repeat" — a design declaring no `replication.repeats` — is false too:
`replication.resolve_repeats` returns one implicit member with `_seed_for(digest, 0)`
(`2122121223` for digest `abc123`), not `derive_seed` (`10901135156558666743`). Both readings fail.
`tests/test_demo.py`'s `self.rng.random()` step exercises the attribute but pins no seed, and
`grep -rn 'self.rng' tests/*.py` is still zero outside it, so nothing catches this.
**Routed:** the sentence must say what the code does (and, since the consequence is that a whole class
of executions shares one stream, that is worth saying rather than eliding); and the `spec-defects.md`
GG entry's *"two further statements … are corrected with them"* plus batch 6's report's *"All four
are corrected to what the code does"* must be corrected — a filing's claim about the code goes stale
like any other comment, and this one was stale the day it was written.

**Major 2 — `CLAUDE.md` § Repository status carries no H9d paragraph, and its order sentence still
names H9d as remaining.** Line 28 reads *"Order of the slices that remain: H9d, then H3c-3's
remaining 14"*, and there are paragraphs for H9a, H9b and H9c but none for H9d. Every merged slice so
far carries one, it is the only place the *retires no refusal / unblocks zero configs* result and the
`E-DOCS-*` mint are recorded outside the slice's own record — and **this is the last slice of the
command surface**, so no later slice would write it. Raised as batch 6's Concern 1, owned by nobody.
**Routed: the controller, before merge.**

**Minor 1 — README's `run` block hard-wraps a line `demo` prints on one line.** README shows

```
          no uv.lock found at ~/publishable-demo; the environment is not
          pinned, and `reproduce` will not be able to restore it
```

and `demo` prints that message as a **single** line — there is no wrapping anywhere in the
diagnostics printer (`grep -rn 'textwrap\|get_terminal_size\|COLUMNS' src/publishable/*.py` finds none
in it). README discloses the path elision (*"Absolute paths are elided to `~` above"*) and not this,
so the transcript contains one line no command emits, in the slice whose purpose is that it contains
none. **Routed:** disclose the wrap in the same sentence as the elision, or unwrap the block.

**Minor 2 — `demo --into <occupied>` prints a diagnostic naming the wrong command.** Behaviour:

```
error E-PROJECT-EXISTS  <dir>
      <dir> already exists and is not empty — `new` never overwrites an existing
      project; choose a different path or remove it deliberately
```

The user typed `demo`. Fix round 2 correctly moved this to exit `1` and correctly reused the shared
code; the shared **message** hard-codes `new`. **Routed:** the message needs the command it is
refusing, or wording that names neither.

**Minor 3 — the dated § Executability entry is pinned to `ebe58ca`, and behaviour moved twice after
it.** Fix round 2 (`9c31d88`) retired three `E-DEMO-*` identifiers and changed `demo`'s occupied-`--into`
refusal from exit `2` to exit `1`. The entry's own sentences survive both, but the feasibility
procedure's step 10 exists so a dated claim can be checked against the commit it names, and at
`ebe58ca` the module did mint three undocumented identifiers. **Routed:** re-date to `9c31d88` or
append the amendment.

**Minor 4 — two pre-existing document facts this slice's own sweeps were positioned to catch, and
did not.** Neither is charged to a task; both are the *sweep for the claim, not for the marker* lesson
fix round 2 itself recorded. (a) § Errors' `E-CODE-DIRTY` row still says *"`run`, and `resume` when it
is built"* while `resume`'s `Status` has read `built` since before this branch — the line is untouched
context in the diff. (b) § Package layout lists `examples/generic/`, which does not exist and carries
no `— not yet built` marker, so the self-maintaining sentence does not cover it.

---

## What I did not reach

- **Check 2's numeric interiors.** I established reproducibility by two full independent runs agreeing
  on every printed digit; I did **not** re-instrument `stats._percentile_ranks` to re-derive the
  6.2e-05 boundary margin or the 3.66e-06 rank-neighbour gap. The batch's method is the right one for
  correction 32 and I am reporting its numbers as **read**, not verified.
- **Check 11's full cross-batch matrix.** I mutated three earlier guards (the region parser's
  duplicate check, `credentials_body`, `FreshSourceFileLoader.get_code`) and each failed loudly. I did
  not re-run the batch's own twelve mutations, nor re-test design § 10 row 14's whole-tree snapshot
  sentinel.
- **The other filings in `spec-defects.md`.** I verified the GG filing (reproduced its measurement and
  found the Major above), confirmed closed entries are **struck rather than deleted**, and confirmed
  the re-owned entries name a fact with a reason. I did not reproduce the `aggregate`, `repeat_spread`,
  attribute-contrast or `run`-prints-nothing filings.
- **`demo`'s stop-4 `dry-run` block against README.** README quotes stops 1, 3 and 5; I diffed those
  three. The 19-line `dry-run` plan is in my capture and in the batch's, and I did not line-diff it
  against `reference.md`'s own transcript.
