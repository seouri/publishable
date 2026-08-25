# H9d tasks 1, 2, 9, 3 — report

**Status: all four complete, branch green.** `uv run pytest` at `0a77e19`:
**3273 passed, 1 skipped, 2 xfailed** (baseline `f9434bf`: 3230 passed, 1 skipped, 2 xfailed,
measured by running before anything moved — +4 task 1, +26 task 2, +5 task 9, +8 task 3).
`ruff check .`, `ruff format --check .` and `mypy` clean at every commit.

| Task | Commit |
|---|---|
| 1 — the guard pin | `697ed31` |
| 2 — the managed-region machinery | `341b491` |
| 9 — the bytecode fix | `30aba16` |
| 3 — the behaviour change | `0a77e19` |
| follow-up (both from the pre-hand-off review) | see below |

**Ruling GG does not bind any of these four.** It binds `base_step.py`, `demo`'s generated step and
§ Randomness. Task 9's third call site is `base_experiment.py`, a different file; `git diff --name-only
f9434bf..HEAD` lists no `base_step.py` and `grep -rn 'self.rng' src/publishable/base_step.py` still
returns its two `random.Random` lines, untouched.

---

## Task 1 — the guard pin: seven arms, editors, and the shape each was captured against

| Arm | Where | Sole authorized editor | Shape captured against |
|---|---|---|---|
| **A** | `tests/test_cli.py::test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` — `[DESIGN_PRINCIPLES]` and `[REFERENCE]` | **NONE** | **Cited, not re-captured.** Already a byte-for-byte scan of both files for `_H5A_ARM_D_LITERALS` |
| **B** | the `[README]` parametrization of that same test | **task 12** | **Cited, not re-captured, and NOT edited.** Post-edit state is the procedure below — *not* a literal tuple |
| **C** | `tests/test_cli.py::test_h9d_arm_c_two_of_the_four_documents_are_byte_identical_at_merge` | **NONE** | **Built.** Whole-file `sha256`, two literals, parametrized by path |
| **D** | `tests/test_scaffold.py::test_h9d_arm_d_every_scaffolded_file_except_the_readme` | **NONE** | **Built.** `{relative path → sha256}` of a `scaffold_project` tree, `README.md` and `.git/` excluded |
| **E** | `tests/test_diff.py::test_h8c_arm_d_readme_worked_diff_block_rows`, `…_design_principles_…`, `…_reference_…` | **NONE** | **Cited, not re-captured** |
| **F** | `tests/test_cli.py::test_h9d_arm_f_the_not_built_command_set` | **task 13** | **Built.** `set(NOT_BUILT_COMMANDS) == {"demo", "docs", "list-templates"}`, plus a **citation** of the shipped `("list-templates", "NOT BUILT")` row assertion in `test_reference_cli_tables_are_parsed_at_all` |
| **G** | `tests/test_validate.py::test_the_worked_examples_intervals_in_reference_md_are_not_narrowed_by_the_null_test_work` | **NONE** | **Cited, not re-captured** (correction 29) |

Arm C's captured digests, at `f9434bf`:
`docs/design-principles.md` → `cf03bdf476973a74c4365f6abdd78ee76aa7754ca2062d02b9c8b785edd80171`;
`docs/experimental-designs.md` → `e4c90c597287a0de9cdbc7cf40980fe325569797bdb7edf9df0cc61b32eccc4d`.
**A red arm C is a finding, not a hash to refresh.**

**Two capture decisions worth naming.** Arm D excludes **`.git/`** as well as `README.md`:
`scaffold_project` runs `git init` and a commit, and index/object bytes are not reproducible between two
runs, so a map including them would pin nothing. Verified by capturing the map **twice in one session**
and comparing before the literal was written (`stable: True`). And the project name is fixed at
`my-study` — `CITATION.cff` and `pyproject.toml` both interpolate it, so a `tmp_path`-derived name would
make the digests machine-dependent.

### Arm B's post-edit state, copied verbatim from design § 8.1

> **Task 12's post-edit state, specified procedurally and in advance:**
>
> 1. Re-scan README with the **unmodified** `_h5a_arm_d_lines_carrying_the_worked_example` helper and the
>    **unmodified** `_H5A_ARM_D_LITERALS` tuple. Neither may be edited.
> 2. The result must equal the pre-edit tuple **minus exactly these four entries** — the three condition
>    rows and the attrition/spread line — **and nothing else**:
>    - `  00_baseline           0.581   [0.488, 0.661]    —`
>    - `  01_method=spearman    0.607   [0.517, 0.683]    +0.026  [−0.007,  0.059]`
>    - `  02_method=kendall     0.412   [0.347, 0.477]    −0.169  [−0.213, −0.125]`
>    - `  intervals over 228 of 240 units (12 failed) · seed spread std 0.014`
> 3. **Every other entry of the pre-edit tuple must survive verbatim**, including
>    `run.yaml → ~/publishable-demo-data/results/run_2026-08-07T09-14-03Z_2f5c8d0/run.yaml` (Decision 2
>    keeps it) and the six `cohort-pilot` lines below it.
> 4. **Any surviving line that is not in that eleven-entry remainder is a finding, not a literal to
>    refresh** — it means a new demo number happens to contain a worked-example literal, and the design
>    owes an answer before the tuple is touched.
> 5. `_H5A_ARM_D_LITERALS` is **not** extended with the demo's new numbers. Arm B pins the *worked
>    example's* numbers; `correlation_pilot`'s are pinned by fixture A instead (§ 9), which asserts them
>    against a real `demo` run rather than against a literal list.

Arm B was **not edited and not re-captured**. Its golden is a **scan result** (correction 28), which is
why no tuple appears anywhere in this report.

### Task 1 mutations — every one full-suite, unfiltered, foreground

Run against the working tree of `697ed31` (the four new arms present) plus the one named change.

| # | Mutation | Result | What failed |
|---:|---|---|---|
| 1 | `docs/reference.md`: `ci95: [-0.213, -0.125]` → `[-0.113, -0.125]` (arm A) | **1 failed, 3233 passed, 1 skipped, 2 xfailed** | `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text[REFERENCE]` |
| 2 | `README.md`: `[0.517, 0.683]` → `[0.517, 0.685]` in the spearman row (arm B) | **1 failed, 3233 passed, 1 skipped, 2 xfailed** | `…[README]` |
| 3 | a blank line appended to **both** `docs/design-principles.md` and `docs/experimental-designs.md` (arm C, both halves in one run — two independent parametrizations, so attribution is exact) | **2 failed, 3232 passed, 1 skipped, 2 xfailed** | `test_h9d_arm_c_…[docs/design-principles.md]` **and** `…[docs/experimental-designs.md]` |
| 4 | `scaffold.CITATION`: `cff-version: 1.2.0` → `1.2.1` (arm D) | **1 failed, 3233 passed, 1 skipped, 2 xfailed** | `test_h9d_arm_d_every_scaffolded_file_except_the_readme` |
| 5 | `NOT_BUILT_COMMANDS` gains a fourth key `"teleport"` (arm F) | **2 failed, 3232 passed, 1 skipped, 2 xfailed** | `test_h9d_arm_f_the_not_built_command_set` **and** `test_reference_cli_tables_are_parsed_at_all` — the second is the shipped set-equality against § CLI reference's own table (correction 26's neighbourhood), attributed rather than counted |

Every revert was made by **copying the pre-mutation file back** — never `git checkout --` — and
verified by **re-running the affected tests green**, then by `git diff --stat` showing test files only.

---

## Task 2 — the region parser, refused in both directions

`src/publishable/docs.py`: `MANAGED_REGIONS` (`overview`, `credentials`, `experiments`, `templates`),
`regions(text)`, `body_of(text, name)`, `rewrite(text, name, body)`, `read_readme(repo_root)`.
Nothing dispatches; `cli.py`, `scaffold.py` and every generator untouched (task 2's commit
`341b491` touches exactly `src/publishable/docs.py` and `tests/test_docs.py`).

**The refusal direction — five codes, each proven with its own file.** Fixture B is five READMEs, one
condition each, and the four structural ones each carry **one well-formed `overview` region beside the
broken one**, so a refusal cannot pass by the file being empty; the `E-DOCS-NO-REGIONS` file cannot
carry one by definition and carries prose plus a **fenced** copy of a real region instead — which makes
it a second test of the fence exclusion, since a fence-blind parser finds `overview` there and does not
refuse at all. Each arm asserts **the code and the message**, because the message is what task 7 prints
on stderr and a refusal that names the wrong region leaves a user nothing to fix.

| Condition | Code | Message asserted |
|---|---|---|
| `begin` with no `end` | `E-DOCS-REGION-UNBALANCED` | ``` `credentials` begins and never ends ``` |
| `end` with no `begin` | `E-DOCS-REGION-UNBALANCED` | ``` `templates` ends without ever beginning ``` |
| two `begin`s, one name | `E-DOCS-REGION-DUPLICATE` | ``` `overview` is opened twice ``` |
| a name core does not manage | `E-DOCS-REGION-UNKNOWN` | ``` `summary` is not a region core manages ``` |
| none of the four | `E-DOCS-NO-REGIONS` | `declares none of the managed regions` |
| no `README.md` at the root | `E-DOCS-NO-README` | `rewrites the managed regions` |

**The honouring direction, which is the half a refusal test cannot see.**
`test_a_readme_holding_some_of_the_four_is_not_a_refusal` — a README with one region parses, and is
rewritable. `test_rewriting_a_region_with_its_own_body_is_the_identity` (× 4) — the round trip
`rewrite(text, name, body_of(text, name)) == text`, byte for byte. `test_a_rewrite_replaces_the_span_
and_moves_no_other_byte` (× 4) — a **different** body, asserted as a whole-file comparison against an
independently spliced expectation, with `out != text` first so it cannot pass for a no-op.
`test_read_readme_returns_the_file_and_refuses_its_absence` asserts both halves in one test.

**The hand-written-prose survival case**
(`test_hand_written_prose_and_the_fenced_decoy_survive_all_four_rewrites`) is built as the case where
prose *would* be destroyed: fixture C carries prose above, between and below every region, plus an
eight-line fenced decoy — a **four-backtick** markdown fence containing a three-backtick `bash` fence
and a full `experiments` region, which is the documents' own shape (§ The generated README fences a
README that fences a `bash` block). All four regions are rewritten in one pass, every prose line and
every decoy line is asserted present, the decoy's block is asserted contiguous, and the four bodies are
asserted **changed** — the control that stops the whole test from passing for a rewriter that did
nothing. The fence rule implemented is CommonMark's: closing fence of the same character, at least as
long, no info string.

### Task 2 mutations — full-suite, at the working tree of `341b491`

| § 10 row | Mutation | Result | What failed |
|---|---|---|---|
| 1 | the `end`-marker search replaced by *rest of file* (`spans[open_name] = (open_at + 1, len(lines))`) | **8 failed, 3252 passed** | all four `…moves_no_other_byte`, the prose-survival test, the fixture-C region test, the trailing-newline test, the empty-body test |
| 2 | the fenced-block exclusion dropped from `_marker_lines` | **14 failed, 3246 passed** | the eight above plus both `no-regions` arms and the four round-trip parametrizations |
| 3 | **replacement, stated below** — the `begin`-with-no-`end` `raise` replaced by `pass` | **1 failed, 3259 passed** | `test_fixture_b_each_malformed_readme_is_its_own_named_refusal[begin-with-no-end]` (`DID NOT RAISE`) |
| 4 | a README missing one region made a refusal (`if set(spans) != set(MANAGED_REGIONS)`) | **6 failed, 3254 passed** | `test_a_readme_holding_some_of_the_four_is_not_a_refusal`, `test_rewriting_a_region_this_readme_does_not_declare_is_a_refusal`, and four `…well_formed_neighbour…` arms |

**Row 3 is a replacement, and the reason is stated in advance rather than after the fact.** As written
it is *"turn `E-DOCS-REGION-UNBALANCED` into a `return EXIT_OK`"* and asserts *"the code and the stderr
line"* — but task 2 ships **no dispatch**, no exit code and no stderr, and the brief forbids touching
`cli.py`. The replacement is the same silence at the level this task ships: the raise becomes a
`pass`, and the assertion checks the **code** and the **message** (the string that becomes task 7's
stderr line). The message half was proven separately, by a targeted micro-mutation — the message
changed from ``region `{open_name}` begins and never ends`` to ``a region begins and never ends``,
which fails the same arm (`1 failed, 25 passed`, `tests/test_docs.py` only). **That one is labelled
non-prescribed and was not run full-suite**; the four prescribed rows above all were.

Row 4's named catcher, *"the 'rewrites what it finds, names what it did not' test"*, is likewise task
7's. Its task-2 stand-in is `test_a_readme_holding_some_of_the_four_is_not_a_refusal`, which is the
parser-level half of the same claim.

---

## Task 9 — the bytecode defect, reproduced, and a measured disagreement with the design

**Reproduced at HEAD first (correction 24), by running, outside the suite.** The filing's own recipe in
the scratchpad: write a module at a path, import it, overwrite the **same path** with different content,
import again. Two arms in one script — `spec_from_file_location(name, path)` and an **explicit
`importlib.machinery.SourceFileLoader(name, str(path))`** — printed:

```
implicit f_probe f_probe
explicit f_probe f_probe
```

**Decision 10's CHOICE was honoured, not overruled.** Option (a) over option (b), and over
`sys.dont_write_bytecode`, is exactly what shipped; only the *implementation* the decision proposed for
option (a) was corrected, because it was measured to do nothing. Nothing in this batch re-litigates
which option the slice takes.

**So option (a) as literally worded is a no-op, and this is the report's main finding.** Both filings
and design Decision 10 propose *"handing it a fresh `importlib.machinery.SourceFileLoader(module_name,
str(path))` explicitly"* — but `spec_from_file_location` on a `.py` path **already returns exactly that
class**, so the explicit form is the same object by another route, and the filing's own recipe still
answers `f_probe` under it. The filing hedged (*"more likely"*); the design inherited the guess.

**What was built is option (a)'s substance — force recompilation — not a rejection of it.**
`src/publishable/sourceimport.py`:

- `FreshSourceFileLoader(SourceFileLoader)` overrides **`get_code`** to go straight from `get_data` to
  `source_to_code`. `get_code` is the method that reads and writes `__pycache__`, so this neither reads
  nor writes it. Measured on the same recipe: `subclass f_probe g_probe`, `pycache files: []`.
- `fresh_spec(...)` for the file-path call site, `import_module_fresh(dotted_name)` for the two
  `import_module` call sites — the latter walks each dotted part through `PathFinder` against its
  parent's `__path__`, swaps in the fresh loader for source files only, and **raises the import
  system's own `ModuleNotFoundError` with `.name` set to the part it could not find**, because
  `PathFinder.find_spec` answers a missing module with `None` and both callers discriminate on exactly
  that `.name`.

It keeps Decision 10's own ground for rejecting `sys.dont_write_bytecode`: this is **per-load**, not
module-global. That is asserted, not merely argued —
`test_the_fix_is_not_sys_dont_write_bytecode_and_leaves_it_alone` checks the flag is untouched **and**
that an ordinary import in the same process still writes its `.pyc`.

**The exception mapping was the real hazard and it is pinned by the shipped suite.** `render_with_
override`'s three refusals and its *no override* arm all discriminate on `ModuleNotFoundError.name`;
`grep -rn 'E-REPORT-OVERRIDE-IMPORT\|-CLASS\|-ENTRYPOINT\|E-ENTRYPOINT-IMPORT' tests/*.py` attributes
the coverage: 3 hits `-CLASS` and 2 hits `-IMPORT` and 1 `-ENTRYPOINT` in `tests/test_report.py`
(including `test_report_module_importing_a_missing_dependency_is_also_e_report_override_import`, the
sibling-import arm), 6 in `tests/test_validate.py` and 2 in `tests/test_acceptance.py` for
`E-ENTRYPOINT-IMPORT`, 1 in `tests/test_cli.py`. All green at `30aba16`.

### Fixture E, and why it does not depend on the clock

Three arms, one per call site, each exercising the **production** entry point (`discover_local`,
`render_with_override`, `load_experiment`) rather than the loader. Each rewrites the file **at the same
byte length** — asserted in the helper, since a different-size rewrite is picked up even unfixed — and
then **pins the first write's `st_mtime_ns` onto the second with `os.utime`**. Without that, a second
boundary falling between the two writes makes the arm pass for a reason unrelated to the code, which is
the flakiness the filing itself describes. Plus two controls: the `dont_write_bytecode` test above, and
`test_a_project_whose_steps_a_run_imports_still_runs_end_to_end`, a real scaffolded project generated,
committed and **run**, so a dotted import chain (`experiment` importing its own `steps/`) is exercised.

### Task 9 mutations — full-suite, at the working tree of `30aba16`

| § 10 row | Mutation | Result | What failed |
|---|---|---|---|
| 5 | the fix reverted at **all three** sites (back to `spec_from_file_location` / `importlib.import_module`) | **3 failed, 3262 passed** | all three site arms |
| 6a | reverted at **`templates/discovery.py` only** | **1 failed, 3264 passed** | `test_discover_local_serves_the_second_write_not_the_first` |
| 6b | reverted at **`report.py` only** | **1 failed, 3264 passed** | `test_render_with_override_serves_the_second_write_not_the_first` |
| 6c | reverted at **`base_experiment.py` only** | **1 failed, 3264 passed** | `test_load_experiment_serves_the_second_write_not_the_first` |

Row 6 is the one that matters and it is proven three ways: each site's revert fails **exactly one
distinct test**, so a sweep that stopped one file short would show here.

The two `spec-defects.md` entries were **not** rewritten — task 14 strikes them, and the entries' own
claims now need re-reading against this code (see *For later tasks*).

---

## Task 3 — the behaviour change, README before and after

**(a) The move.** `README`, `CITATION`, `MIT`, `GITIGNORE` are now
`src/publishable/readme_templates/{README.md.tmpl, CITATION.cff.tmpl, LICENSE.mit.tmpl, gitignore.tmpl}`,
read at scaffold time by `scaffold.read_scaffold(filename)` through `importlib.resources` (so an
installed wheel answers like a source checkout). The four files were **generated programmatically from
the imported constants**, never retyped, so no trailing newline could drift. `scaffold.py` keeps both
`.format(name=…)` calls and every refusal; `PYPROJECT` stays a module global (not in scope).

`plugin_scaffold.py` imported three of the four (`from publishable.scaffold import CITATION, GITIGNORE,
MIT`) and now calls `read_scaffold` instead — its own `README` global is a different, plugin README and
is untouched. `grep -rn "scaffold import" src/ tests/` attributes every importer:
`cli.py:100` (`scaffold_project`), `cli.py:61` (`scaffold_plugin`), `plugin_scaffold.py:19`
(`read_scaffold`, mine), `tests/test_plugin_scaffold.py:8`, `tests/test_scaffold.py:12` and `:353`
(`read_scaffold`, mine). `tests/test_plugin_scaffold.py` is green unchanged, which is the claim that
the plugin scaffold's bytes did not move.

**Packaging, verified by installing rather than by reading.** `pyproject.toml` gains
`artifacts = ["src/publishable/readme_templates/*.tmpl"]` under
`[tool.hatch.build.targets.wheel]`. `uv build --wheel` then `unzip -l` lists all four `.tmpl` files;
the wheel was installed into a **fresh venv** (`uv venv` + `uv pip install`) and
`publishable new my-study` was run **outside this repository**, in the scratchpad, producing a project
whose README carries all four regions. *Measured, and worth recording:* hatchling already ships them
under `packages = ["src/publishable"]`, so the declaration is belt-and-braces rather than the thing
that made it work — it force-includes them even if the pattern is ever VCS-excluded.

**Guard-pin arm D stayed green across move (a)** — its editor is NONE and it was not touched — and the
scaffolded README was **byte-identical after (a) alone**
(`sha256 523cfded…` before and after, 481 bytes), which is the claim that (a) moved *where* the bytes
are read from and nothing else.

**(b) `scaffold.README` becomes what § The generated README specifies.** Captured before and after by
scaffolding into the scratchpad and diffing the bytes: **481 → 1392 bytes**, `sha256 523cfded…` →
`e4207b5d…`. (An intermediate cut at `0a77e19` was 1434 bytes / `228cc4b3…`, with a two-column
`Template | Parameters` header in the `templates` region; the follow-up commit below replaced it with
the bare empty-state line, for the reason in item 4.) The complete diff, and there is nothing else in it:

1. `cp .env.example .env    # then fill in the values below` added inside the `bash` Setup fence;
2. the **`credentials` region** added, with `### Required credentials` and the documented two-column
   `Variable | Needed by` table and its `_(none yet — added as experiments declare them)_` empty row;
3. `## Experiments` **moved from above the `begin` marker to inside the region**, and the prose line
   `None yet. Create one with \`publishable generate experiment <name>\`.` replaced by the documented
   `Name | Template | Run` table with its `_(none yet — add one with \`publishable generate
   experiment\`)_` empty row;
4. a **`templates` region** added — correction 17's fifth drift; the four documents declare one nowhere
   and § Templates needs one — carrying `## Templates` and a bare
   `_(none yet — add one with \`publishable generate template\`)_` line. **Deliberately not a table
   header**: § Templates renders a populated `templates` region as one *sub-section per template*
   (`### \`<name>\``, a convention line, a five-column `parameter_spec` table), so a two-column
   `Template | Parameters` header would declare a schema the populated form never writes — the
   *declared vs. derived* drift — and would be a header task 6 had to delete before writing anything.
   Pinned by `test_the_templates_regions_empty_state_is_what_a_populated_one_degenerates_to`;
5. the **`## Reproducing a published result`** section added verbatim from the document, including the
   `uv run --with publishable publishable reproduce run.yaml` line.

**`scaffold.GITIGNORE` does not change**, and that is asserted rather than left implicit:
`test_the_scaffolded_gitignore_still_says_nothing_about_demo_progress` pins the absence of
`.demo-progress` beside the presence of `.env` and `__pycache__/`, so it cannot pass by the file being
empty. The **documented sentence** is what moves, and it is task 14's.

**Task 3 mutation — full-suite, at the working tree of `0a77e19`.** One byte of the **`credentials`
region body** changed (a second space before the closing pipe of the empty row):
**1 failed, 3272 passed, 1 skipped, 2 xfailed** —
`test_each_scaffolded_region_body_is_what_the_document_specifies[credentials]`, which **names the
region**, read back through `docs.body_of` rather than through a whole-file digest. Guard-pin arm D
stayed green under it, as it must: arm D excludes `README.md`.

---

## What was grepped, and what every hit was

Newline-insensitive where the claim spans lines; **file lists filtered, never sweep output**.

1. `grep -rn "publishable:begin\|publishable:end" src/` — **correction 18 re-checked before building.**
   Before task 2: four lines, all `src/publishable/scaffold.py`, no parser. After task 3: 1 hit in
   `src/publishable/docs.py` (the module docstring quoting the marker) and 8 in
   `readme_templates/README.md.tmpl` (four regions × two markers). `scaffold.py` no longer carries any,
   because the constant became a file.
2. `grep -rn "E-DOCS-" src/ tests/ README.md docs/reference.md docs/design-principles.md
   docs/experimental-designs.md` — 16 hits `src/publishable/docs.py`, 10 hits `tests/test_docs.py`,
   **zero in any document**. So the five codes are new and **no § Errors row exists for any of them
   yet** — task 14's.
3. `grep -n "sourceimport\|readme_templates\|docs\.py" README.md docs/reference.md
   docs/design-principles.md docs/experimental-designs.md` — two hits, both `docs/reference.md`
   § Package layout: the `docs.py … — not yet built` row and the `readme_templates/` row. **No row
   anywhere for `sourceimport.py`** — task 14's, see below.
4. `grep -rn "def test_h8c_arm_d" tests/test_diff.py` — three functions
   (`…_readme_worked_diff_block_rows`, `…_design_principles_…`, `…_reference_…`). Arm E cited, and it
   exists.
5. The body of `test_the_worked_examples_intervals_in_reference_md_are_not_narrowed_by_the_null_test_work`
   read whole: its only file read is `docs/reference.md`; the two `README` mentions are **in the
   docstring**, saying it deliberately leaves README's `[0.347, 0.477]` unpinned. **Correction 29
   confirmed against the code, not carried.**
6. `grep -rn "scaffold import\|import CITATION\|import GITIGNORE\|scaffold\.README\|scaffold\.MIT"
   src/ tests/` — six hits, each attributed in the task 3 section above. `plugin_scaffold.py:19` was
   the only production importer of the moved constants.
7. `grep -rn "E-REPORT-OVERRIDE-*\|E-ENTRYPOINT-IMPORT" tests/*.py` — 15 hits, attributed in the task 9
   section. Every arm the fix could have broken has a shipped test.
8. `git diff --name-only f9434bf..HEAD` — sixteen files, no `base_step.py`, no `cli.py`, no document
   among the four, no guard-pin arm A/B/E/G. `grep -rn 'self.rng' src/publishable/base_step.py` — two
   hits, both `random.Random`, untouched (ruling GG is not these tasks').

---

## For later tasks — carried, not fixed here

- **Task 14 owes five § Errors rows**: `E-DOCS-REGION-UNBALANCED`, `-DUPLICATE`, `-UNKNOWN`,
  `E-DOCS-NO-REGIONS`, `E-DOCS-NO-README`. **And `E-DOCS-REGION-UNKNOWN` carries two senses**, so its
  row must say both: *a region name core does not manage*, **and** *a managed name this README does not
  declare*, which `rewrite` refuses rather than skipping (Ruling EE applied to the rewriter). A sixth
  code was deliberately not minted for the second sense.
- **Task 14 owes a § Package layout row for `src/publishable/sourceimport.py`**, a new module. The
  `readme_templates/` row is now true as written; `docs.py`'s `— not yet built` marker is task 14's to
  drop once task 7 wires the command.
- **Task 14, the two bytecode filings:** both name option (a) as *"an explicit `SourceFileLoader`"*.
  **That wording is false of the fix and was false of the guess** — see the measurement above. Strike
  them with the correction stated, not with a claim that the proposed remedy was applied.
- **Task 5** should read the `experiments` region body this slice ships (`## Experiments` + the
  `Name | Template | Run` table) as its empty state, and **task 6** the `templates` one
  (`## Templates` + `Template | Parameters`). Both are pinned by
  `test_each_scaffolded_region_body_is_what_the_document_specifies`, which those tasks will need to
  update if the generated empty state changes — it is **not** a guard-pin arm and has no NONE editor.
- **`reference.md` § The generated README shows three regions, not four.** The scaffold now writes the
  `templates` one (Decision 9's fifth drift). The document edit is task 14's; nothing in this batch
  compares the scaffolded README to that fenced block, deliberately, because such a test would go red
  on a document this batch may not touch.

## Concerns

1. **The design's Decision 10 is wrong in its mechanism** (not in its choice). Anyone re-reading it will
   find *"explicit `SourceFileLoader`"* and, if they re-derive from that sentence, will ship a no-op
   that passes review because it looks like the design. The design is a spec and may not be
   retro-edited; this report and the commit message are where the correction lives, and task 14 should
   carry it into the two filings.
2. **`import_module_fresh` forces recompilation of the modules IT resolves.** A module the loaded file
   imports itself — a sibling step, a vendored helper — goes through the ordinary import system and can
   still be served from `__pycache__` within one second. Both filings are about the entrypoint/override/
   template file itself, so this is beyond them; a meta-path finder would cover it and was deliberately
   **not** built, because it makes design § 10 row 6 (*revert at exactly one of three sites*)
   unexhibitable. **Filed here rather than built**, unowned after this slice.
3. **Fixture E depends on `os.utime` with `ns=` being honoured by the filesystem.** It is, on this
   machine and on tmpfs; on a filesystem that silently coarsened it, the three arms would pass without
   testing anything — which is why the helper asserts the mtime it set was actually kept.


---

## Follow-up commit, after the pre-hand-off review

Two things, both caught by review rather than by a mutation, both cheap, one full-suite run
(**3282 passed, 1 skipped, 2 xfailed**; +9 over `0a77e19` — 8 new round-trip parametrizations and the
one new `templates` empty-state test).

1. **The `templates` region's empty state became a bare line rather than a two-column table header** —
   the *declared vs. derived* drift described in task 3 item 4 above. `README.md.tmpl`,
   `_TEMPLATES_BODY` in `tests/test_scaffold.py`, and one new test naming the reason.
2. **The round trip is now pinned on a file with NO trailing newline, and on a region whose own last
   line is blank** — the two shapes where `rewrite`'s line-splice convention and `body_of`'s could
   disagree. Measured before the arm was written: the identity **already held** for all four regions of
   both shapes, so this is a pin of an existing property rather than a fix — recorded that way rather
   than as a defect closed.
