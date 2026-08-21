# Task report: batch 5 — tasks 7, 8 (`covered_config`'s delta walk; `diff.py`'s form
detection, header, four rows)

Dated 2026-08-20, measured against the commit each task built on. Suite: 2580 → **2587** (task 7)
→ **2600** (task 8). `uv run mypy` → 48 → **49** source files, clean throughout. `uv run ruff
check .` → clean throughout. `uv run ruff format --check .` → 86 → **88** files (`diff.py`,
`tests/test_diff.py`), unchanged between the two commits.

## Status: done, both tasks, two commits

- `986f10a` — task 7: `covered_config` extracted, and the parameter delta walk over it
- `ed615e4` — task 8: `diff.py` — form detection, the per-side header, the four rows

Neither task's own brief was found to disagree with the plan's Interfaces sections or with
Decisions 1-6; no task decomposition dispute to disclose this batch.

## Task 7 — `covered_config` extracted, `parameters_hash` rewritten to call it

`hashes.covered_config(config)` is the exact projection `parameters_hash` computed inline —
every top-level key except `metadata`, `data` narrowed to everything but `input_dir`/`output_dir`.
`parameters_hash` now hashes `covered_config(config)`'s canonical JSON rather than reimplementing
the projection. Every shipped `test_hashes.py` test is **unchanged and still passes** — the second
pin, beside the extraction itself, that `parameters_hash`'s behaviour did not move.

**Does not normalize, and does not claim to.** `covered_config`'s docstring cites
`docs/superpowers/spec-defects.md` § "`parameters_hash` does not normalize to what `init` would
have materialized" **by its own title**, does not restate its content, and does not strike it —
grepped by name in `spec-defects.md` (`grep -n "parameters_hash" docs/superpowers/spec-defects.md`)
to confirm the entry is still present, OPEN, owned by H6, after this commit.

`diff.py`'s delta walk (`parameter_deltas`, `_flatten`, `_render_leaf`) flattens
`covered_config`'s return on **both** sides to dotted leaf paths; a `dict` is recursed, anything
else — including a `list` — is a leaf. Rendering: `(absent) → <value>` when a leaf exists on only
one side, one line of untruncated `yaml.safe_dump(..., default_flow_style=True)` for a list/dict
leaf, `str(value)` for a scalar, sorted by path.

### Fixture M, the pair, and why only the pair discriminates

Two arms, both at the function level (`parameter_deltas`, no `run` needed):

- **Arm one** (`test_h8b_fixture_m_arm_one_metadata_only_edit_is_zero_delta_lines`): two records
  differing only in `metadata.description` → **zero** delta lines.
- **Arm two** (`test_h8b_fixture_m_arm_two_limits_only_edit_is_exactly_one_line`): two records
  differing only in `limits.max_failed_fraction` → **exactly one** line, both values read back from
  the two dicts (`a["limits"]["max_failed_fraction"]` / `b[...]`, never typed).

**This is the pair that proves the hash and the delta walk agree about coverage, and a
single-reader fixture would not.** `parameters_hash` and `parameter_deltas` both call
`covered_config` — one projection, two readers — so a walk that silently narrowed its own
coverage (to `config["parameters"]` alone, say) would still pass arm one (metadata was never in
`parameters` either way) while failing arm two, *without either function's own unit tests
noticing*: `parameters_hash`'s shipped tests only ever assert equality/inequality of the **hash**,
never inspect what a delta walk would print over the same edit, so a coverage-narrowing bug in a
second, independently-built delta list could ship with the hash-only tests still green. Building
the pair (not just arm two alone) is what shows arm one is not merely also-passing by coincidence
of the narrowed set — it is the control that keeps M4 (below) from looking like it discriminates
when it only fails the second arm.

A third arm (`test_h8b_fixture_m_arm_three_a_reordered_list_is_one_line_not_indexed`) pins the
list-is-a-leaf rule with a reordered `sweep.grid` axis list: exactly one line, not one per moved
position.

### Mutations run, reverted, and reported by name

**M4 — narrow the delta walk to `config["parameters"]` alone.**
`flat_a = _flatten(covered_config(config_a))` → `flat_a = _flatten(config_a.get("parameters") or
{})` (and the `_b` twin).
- Ran `uv run pytest tests/test_diff.py tests/test_hashes.py`: **5 failed, 36 passed.**
- **Arm one passed under the mutation** (not in the failure list) — confirming the brief's own
  prediction that a narrowed walk still passes the metadata arm, which is exactly why only the pair
  (not arm two alone) proves the two branches differ on coverage rather than on something else.
  A property-preserving arm (arm one) does what it should here: nothing about "does `metadata`
  move the hash" changed, so it stays green regardless of which projection the walk uses — the
  narrowing only bites once a *covered, non-`parameters`* field is edited, which is arm two and
  three of Fixture M's own construction.
  Arm two failed (`0 == 1` delta lines expected), as did the sorted/absent/reordered-list tests and
  the real-run Fixture R2 test. Fixture R2's failure is worth being precise about, since
  `min_samples` genuinely lives under `parameters` and the mutation still sees a value there:
  `M4`'s mutation flattens the **`parameters` sub-dict directly, with no prefix**, so the emitted
  path becomes `analysis.min_samples`, not `parameters.analysis.min_samples`. The test's own filter
  (`line.strip().startswith("parameters.analysis.min_samples")`) then matches **zero** lines — not
  because the value disappeared, but because the path lost its `parameters.` root. That is still a
correct catch of the mutation (the delta line it prints is wrong), just not for the reason a first
skim suggests.

**Second mutation — recurse into a list by index** (task 7 step 6). `_flatten` gained an
`elif isinstance(value, list): out.update(_flatten({str(i): v for i, v in enumerate(value)},
prefix=f"{path}."))` branch.
- Ran the same two files: **2 failed, 39 passed.**
- Failing: the reordered-list arm (`assert 2 == 1` — two per-position lines instead of one) and the
  absent-arrow test (`statistics.contrasts.0.a (absent) → 1` instead of
  `statistics.contrasts (absent) → [{a: 1}]`).
- **Why the two branches differ, checked rather than assumed:** under the leaf rule a reordered list
  is ONE line (the whole list moved); under the index rule it is one line per moved position — here
  two, matching the brief's own prediction that the **line count**, not the verdict, is the
  discriminator (`parameters_hash` over the reordered list moves under both branches, since
  canonical JSON preserves order either way).
- Reverted; `diff /tmp/diff.py.orig src/publishable/diff.py` → **identical**; re-ran → **41 passed**.

## Task 8 — form detection, header, four rows, refusals

`diff.command_diff(a: Path, b: Path) -> int`, a direct call only — `diff` is not wired to
`cli.main` until task 11, so every refusal here is handled (or deliberately left to propagate)
inside `command_diff` itself rather than by `main`'s generic catch.

**Form, by shape, before any parsing:** a directory, or a file named `run.yaml`, is a run record
(dispatched to `lineage.read_run_record` on the run directory — its parent, if given the file
itself); any other path (existing or not) is a config. Grepped `read_run_record`'s own docstring
and body in `src/publishable/lineage.py` to confirm it is directory-keyed and appends `run.yaml`
itself, matching the brief's own measurement.

**Three refusal groups, each checked against the actual body of the function it names, not
assumed from the brief's prose:**
- A missing path: `_read_config`'s `path.read_text()` raises `FileNotFoundError`, uncaught inside
  `command_diff` — grepped `freeze.py`'s `_precheck` docstring ("validate's own precedent for a
  path problem it did not anticipate is to let the `OSError` propagate") and `cli.py`'s `main`
  (`except OSError as exc: ... code="E-IO-FAILED"`) to confirm this is the shipped precedent being
  followed, not invented. Test asserts `pytest.raises(OSError)` directly on `command_diff`, since
  `main` is not in the loop yet.
- An unreadable **record**: `read_run_record` already raises `ContractError` with
  `E-UPSTREAM-RECORD-MISSING`/`-UNREADABLE`/`-VERSION` — read the function body in
  `src/publishable/lineage.py` line by line rather than assuming from its docstring alone; no new
  code needed. `command_diff` catches `ContractError` from either side's `_load_side` call and
  prints+returns `EXIT_WRONG`.
- An unreadable **config**: the one new code, `E-DIFF-CONFIG-UNREADABLE`, minted in `_read_config`
  for a YAML parse failure or a document that doesn't parse to a mapping.

**Header:** `A`/`B`, the form, the identity, and — for a run record — its `status` plus the word
`draft` when `draft: true`. A config side prints its form and `str(path)` **as given** (never
`.resolve()`d), and no status word.

**Four rows** (`code_hash`, `input_manifest`, `uv.lock`, `parameters_hash` — `apparatus` is task
9's, so `ROW_LABELS` is four long here; its module-level comment names task 9 as the row list's
one authorized future editor, inserting `'apparatus'` fourth). Verdicts: `identical` +
`sha256:XXXX…` (4 hex chars, one `…`), `DIFFERS` (+ the two digests, or task 7's deltas for
`parameters_hash`), `not captured` when the figure is `null` on **either** side.

### The `uv_lock_hash: None` reproduction, before and after

**Before** (measured by driving two independent scaffolded runs through `main(["run", ...])` and
reading `run.yaml` back): `provenance.environment.uv_lock_hash` is `None` on **both** — a
scaffolded project resolves no lockfile.

**Naive form, reproduced under mutation M1** (see below): with the null-guard removed, `_render_row`
falls through to `figure_a == figure_b` (`None == None` is `True`) and printed literally
`uv.lock    identical    sha256:None…` — the exact dangerous output Decision 1 names, reproduced
against a real two-run pair, not asserted from the design doc's prose alone.

**After** (current code, same two-run pair): `uv.lock    not captured` — verified both via the
Fixture R2/L tests and via a standalone `uv run python3` repro run against two independent
`build(tmp_path)` scaffolds (recorded in this batch's working notes; both runs' `uv_lock_hash` read
back `None`, and `command_diff` printed `not captured`, never `identical`).

### Fixture R2 and Fixture L, what each pins and why L is needed

**R2** (`parameters.analysis.min_samples` moved by 20, nothing else, on the *same* project via a
second `main(["run", ...])` against an edited config copy): `code_hash`/`input_manifest`
`identical`, `uv.lock` `not captured`, `parameters_hash` `DIFFERS` with **exactly one** delta line
(`min_samples: <before> → <before+20>`, both values read back from the two `config.yaml` copies),
exit `0`.

**L** (a real `uv.lock` written and committed via `tests/test_acceptance.py`'s `build` helper,
before the run, then a byte change and a re-commit before a third run): pins `uv.lock`'s
`identical` arm (two runs sharing one lockfile) and its `DIFFERS` arm (the lockfile's bytes moved
between runs) — **the only fixture in this batch that reaches either arm**, since every
`run_a_project`-scaffolded run takes `not captured`. Verified both `uv_lock_hash` values are
non-null and differ appropriately by reading them back from each run's `run.yaml`, never asserted
as literals.

### The row-order pin, and why it is not compared against `ROW_LABELS` itself

`test_h8b_row_order_is_pinned` asserts the **printed** sequence of row labels (extracted from
`command_diff`'s captured stdout by `_row_labels_in_output`) against the **literal**
`["code_hash", "input_manifest", "uv.lock", "parameters_hash"]` — not against the `ROW_LABELS`
constant. Checked directly: if the comparison target were `ROW_LABELS` itself, a mutation that
reverses that one constant would move both the actual iteration order (since `command_diff` drives
its row loop from that same constant) and the test's expected value together, making the
assertion vacuously true under exactly the mutation it exists to catch — the "test iterates the
thing under test" shape. A separate, redundant sanity check (`assert ROW_LABELS == [...]`) is kept
above it for documentation, but the row-order mutation below was re-run with that first assertion
disabled to confirm the second, output-based assertion catches the defect **on its own**.

### Mutations run, reverted, and reported by name

**M1 — print `identical` instead of `not captured` when a figure is `null`.** Removed the
null-guard in `_render_row`; `figure_a == figure_b` (both `None`) now falls into a hand-built
"identical" line mimicking the naive bug.
- Ran `uv run pytest tests/test_diff.py tests/test_hashes.py`: **1 failed, 40 passed** — failing:
  `test_h8b_fixture_r2_the_documented_payoff`, whose assertion is the **literal string**
  `"uv.lock    not captured"`. Captured stdout under the mutant:
  `uv.lock    identical    sha256:None…` — confirming the mutation is not blind on the
  two-null-sides arm, and reproducing the exact dangerous line named above.
- **One-sided variant, checked manually** (not as a committed test, per the brief's own framing —
  "confirm it too reports `not captured`", checked by direct script rather than by adding a second
  committed arm this batch): a run with a real, non-null `uv_lock_hash` (Fixture L's `run_a`)
  against a run with `uv_lock_hash: None` (a separate scaffold's run) — under the mutant this
  **crashes** (`AttributeError: 'NoneType' object has no attribute 'partition'` inside `_truncated`,
  reached via the `DIFFERS` branch's two-digest line) rather than silently printing a false
  verdict. Reported as: the guard's removal is non-blind on both arms, though the one-sided arm's
  failure mode is a crash rather than a second false-`identical` — worth noting because a different
  naive implementation (formatting the raw hash without `_truncated`) could produce a false
  `DIFFERS "sha256:None… → sha256:8e21…"` line instead; that variant was not separately re-verified
  this batch.
- Reverted; `diff /tmp/diff.py.orig src/publishable/diff.py` → **identical**; re-ran → **41
  passed**.

**Row-order mutation.** `ROW_LABELS` reversed to
`["parameters_hash", "uv.lock", "input_manifest", "code_hash"]`.
- Ran the same two files: **1 failed** (`test_h8b_row_order_is_pinned`), on the first
  (redundant) assertion.
- Re-ran with that first assertion temporarily commented out to confirm the **second**,
  output-based assertion fails **on its own**: it does — `['parameters_hash', 'uv.lock',
  'input_manifest', 'code_hash'] != ['code_hash', 'input_manifest', 'uv.lock', 'parameters_hash']`.
  Restored the commented line immediately after (not left disabled).
- Reverted `ROW_LABELS`; `diff /tmp/diff.py.orig src/publishable/diff.py` → **identical**; re-ran
  → **41 passed**.

## What was grepped, and its scope

- `grep -n "parameters_hash"` over `docs/superpowers/spec-defects.md` (whole file) — confirmed the
  normalization filing's exact title and OPEN/H6 status, before citing it by title in
  `covered_config`'s docstring, and again after committing to confirm it was not struck.
- `grep -n "code_hash\|input_manifest\b\|uv\.lock\b\|parameters_hash\b\|DIFFERS\|identical\|not
  captured"` over `README.md`, `docs/design-principles.md`, `docs/reference.md` (all three named
  explicitly, not a bare `*.md` glob) — confirmed all three worked outputs spell the labels
  `input_manifest` and `uv.lock`, never `input_manifest_hash`/`uv_lock_hash`, before hard-coding
  those exact strings in `ROW_LABELS`.
- `grep -n "never captured"` over `docs/reference.md` — found `study add`'s own use of the
  "never captured" vocabulary (redaction section) as the precedent for reusing `not captured`
  rather than minting new wording.
- `grep -n "EXIT_OK\s*=\|EXIT_WRONG\s*=\|..."` over `src/publishable/diagnostics.py` — confirmed
  the five exit code integer values before using them in `diff.py`.
- `grep -n "OPERATION_COMMANDS\|NOT_BUILT_COMMANDS\|def _dispatch\|def main"` over
  `src/publishable/cli.py` — confirmed `diff` has no CLI arm yet and `main`'s generic `OSError`/
  `PublishableError` handling, before deciding `command_diff` must handle its own refusals rather
  than relying on `main`.
- `grep -rn "import diff\|from publishable.diff\|from publishable import diff"` over `src/` and
  `tests/` — confirmed nothing imports `diff.py` yet (no cycle risk to check for this batch).
- `grep -n "^def test_"` over `tests/test_hashes.py` — confirmed task 13's Arm G tests already
  exist under different names than I first assumed, before writing new `covered_config`-specific
  tests rather than duplicating Arm G's own coverage.

No claim of zero disagreements is made beyond what is stated above; the greps listed are the full
set run this batch, each with the file(s) it targeted.

## Full suite, both commits

- After task 7 (`986f10a`): `uv run pytest` → **2587 passed, 1 skipped, 2 xfailed** (2580 + 7:
  2 `covered_config` tests in `test_hashes.py`, 5 Fixture-M-level tests in `test_diff.py`).
  `uv run mypy` → 49 source files (`diff.py` created, containing only the delta walk at this
  point). `uv run ruff format --check .` → 88 files.
- After task 8 (`ed615e4`): `uv run pytest` → **2600 passed, 1 skipped, 2 xfailed** (+13: form
  detection, refusals, header, Fixture R2/L (with row-output variants), row-order pin).
  `uv run mypy` → 49 source files (unchanged — no new module). `uv run ruff format --check .` →
  88 files (unchanged).
- No shipped test outside `test_hashes.py`/`test_diff.py` changed in either commit.

## Concerns for the next batch (task 9)

- `ROW_LABELS`'s docstring and the row-order test's docstring both already name task 9 as the row
  list's one authorized editor, per the plan's own instruction — task 9 should find these comments
  rather than discover the constraint itself.
- `command_diff` currently prints **no row section at all** when either side is a `config` — this
  is deliberate (task 10 owns the config side's `not comparable` vocabulary) and not a bug, but it
  means task 9's own apparatus-row work should keep its fixtures to run-vs-run pairs, matching this
  batch's own scope.
- The one-sided `not captured` arm (non-null vs. null) was checked manually against a hand-rolled
  script this batch, not committed as a test — Fixture L's own two runs are both non-null once the
  lockfile exists, and no fixture in this batch mixes a null-`uv_lock_hash` run against a non-null
  one. **Closed in Fix round 1** (Major 2, below) — this bullet is kept rather than deleted so the
  record shows what the original gap was.

---

## Fix round 1 (2026-08-21)

Review at `.superpowers/sdd/2026-08-20-diff-freeze/task-b5-review.md`. Both verdicts PASS with
findings: four Majors, four Minors. All eight closed. Gates at clean HEAD before this round:
suite 2600 passed / 1 skipped / 2 xfailed, mypy 49, ruff format 88 — all unchanged from the batch
this round fixes. After this round: suite **2609** passed / 1 skipped / 2 xfailed (+9 new tests),
mypy 49 (unchanged — no new module), ruff format 88 (unchanged).

**Credit acknowledged, not re-litigated.** The reviewer's own ten-config digest-stability check,
the M4/list-recursion/row-order re-runs, and the correctness of Decision 3's extraction all stand;
this round only closes what was found wrong.

### Major 1 — `_flatten` dropped an empty mapping

**Changed:** replaced the per-side-independent `_flatten` with `_diff_values(value_a, value_b,
path)`, a DUAL walk over both configs at once. It descends into a `dict` present on EITHER side
(empty or not) by recursing on the UNION of that path's keys; a path becomes a leaf only when
NEITHER side has a child there (both empty, or one absent and the other empty). `parameter_deltas`
now calls this once, sorts the resulting `(path, value_a, value_b)` triples, and renders them with
the same column-aligned format as before.

A simpler patch — just "treat every empty `dict` as a leaf" in the original per-side flatten —
was tried first and **rejected** because it regresses a shipped case: given
`a = {"parameters": {}}` and `b = {"parameters": {"z": {"late": 1}, "a": {"early": 1}}}`, treating
`a`'s empty `parameters` as a leaf makes it appear ONLY on `a`'s side (since `b`'s non-empty dict
never appears as a leaf, only its recursed children do), producing a false extra line
`parameters  {} → (absent)` — wrong, since `b` does not lack `parameters`, it has real content
just represented one level deeper. Caught by re-running `test_h8b_parameter_deltas_are_sorted_by_path`
(already shipped, unrelated to this finding) against that simpler patch before committing to it;
the dual-walk does not have this defect, verified by the same test passing unchanged.

**Verified by:**
- `test_h8b_an_empty_mapping_leaf_prints_one_line_not_a_bare_differs` (pure function, both
  directions) and `test_h8b_fixture_m_arm_four_sweep_empty_block_deleted_end_to_end` (end to end:
  scaffolds a real project, reads back `config_a["sweep"] == {}` — measured, not assumed, from
  `init`'s own output — deletes the key, reruns, and asserts `parameters_hash` differs while
  `parameter_deltas` names exactly one line).
- **Mutation, reverted:** restored the exact pre-fix per-side-independent flatten (kept as
  `_old_buggy_flatten` for the duration of the check) → `2 failed, 48 passed` in
  `tests/test_diff.py tests/test_hashes.py`. The two failures were exactly the two new tests
  above; all 48 property-preserving tests — including every pre-existing Fixture M arm and the
  sorted-path test that the simpler patch would have broken — stayed green, confirming the fix is
  neither blind nor a regression. Reverted by restoring the saved fixed copy; `diff` against it →
  identical; re-ran → 50/50 passed.
- **Digest stability re-verified empirically, not assumed from reading.** `hashes.py` has **zero
  diff** in this fix round (`git diff --stat HEAD -- src/publishable/hashes.py` → empty output),
  so no hash could have moved — but also ran `hashes.parameters_hash` over ten configs (`{}`,
  `{"data": {}}`, `{"data": {"input_dir": "/x"}}` and its `output_dir` twin, `{"metadata": {"x":
  1}}`, `{"sweep": {}}`, `{"data": None}`, `{"data": "not-a-dict"}`, `{"data": ["list"]}`, a
  populated `parameters`+`limits` config) against the pre-fix-round commit (via `git stash` on
  `diff.py`/`test_diff.py` alone, leaving `hashes.py` untouched either way) and the post-fix-round
  tree: **all ten digests byte-identical.**

### Major 2 — the one-sided `not captured` arm was unpinned

**Changed:** no source change — behaviour at HEAD was already correct (`or`, not `and`). Added
`test_h8b_the_one_sided_not_captured_arm`: a real lockfile-backed run (Fixture L's own mechanism,
non-null `uv_lock_hash`) against an ordinary `run_a_project` scaffold (null), through
`_render_row("uv.lock", ...)` in both operand orders.

**Verified by:** mutation `or` → `and` in `_render_row`'s guard → `1 failed, 49 passed`; the new
test failed with the exact crash the review named
(`AttributeError: 'NoneType' object has no attribute 'partition'` inside `_truncated`), and all 49
other tests — including Fixture R2's both-null case, the property-preserving arm this guard's
`and` variant does not touch — stayed green. Reverted; `diff` against the saved fixed copy →
identical; re-ran → 50/50 passed.

Closed now rather than deferred to task 10, per the review's three reasons: the material already
existed in this batch, task 10 owns a different code path (`not comparable`, the config side) and
a different word, and the exposure was a crash.

### Major 3 — Python reprs instead of the config's own YAML vocabulary

**Changed:** `_render_leaf` now special-cases `bool` (→ `true`/`false`) and `None` (→ `null`)
before falling through to `str(value)` for every other scalar — `str` values are untouched, so
this is not a blanket `yaml.safe_dump` widening (a quoted string would be a new, unrequested
change). `bool` is checked before the generic branch because `isinstance(True, int)` is also
`True`, noted in the docstring as future-relevant rather than load-bearing today (there is no
separate `int` branch).

**Verified by:** `test_h8b_bool_and_none_leaves_render_as_yaml_not_python_repr` (both `True`/`False`
and `None`/`"site"` pairs, asserting the YAML spellings appear and the strings `"True"`/`"None"`
do not) and `test_h8b_scalar_string_leaves_are_not_yaml_quoted` (the property-preserving control —
an ordinary string delta must still render unquoted). **Mutation, reverted:** removed the two new
branches → `1 failed, 49 passed`; only the bool/None test failed, the string-scalar control passed
unchanged, confirming the fix is scoped to the two types named and does not touch strings. Reverted;
`diff` → identical; re-ran → 50/50 passed.

### Major 4 — the row-label pin was not built, and a pre-writing grep was presented as its discharge

**Changed:** added `_document_row_labels(path)` to `tests/test_diff.py`, the
`_status_tables`/`_interval_method_names` shape from `tests/test_cli.py` — it parses a fenced
`diff` output for `<label>  identical|DIFFERS` lines, anchored at line-start so an indented detail
line never matches. Three tests: a non-vacuous-parse control over all three documents, an equality
pin against README's and design-principles.md's four-row form, and a pin against reference.md's
five-row form with `apparatus` filtered out. Each compares the DOCUMENT-derived list against
`ROW_LABELS` — the code's own constant — not against a second hard-coded literal, which is the
property Major 4 named as missing (a document rename must be able to fail this).

**Verified by:** re-ran the same grep the review named absent (`grep -rn
'README.md\|design-principles.md\|reference.md' tests/` narrowed to files actually opening those
paths) — before this round, none in `tests/` derived `diff`'s row labels from them; now
`tests/test_diff.py` does. **Mutation, reverted:** changed `ROW_LABELS` to
`["code_hash", "input_manifest_hash", "uv_lock_hash", "parameters_hash"]` (the exact `_hash`-suffixed
misspelling the review used as its example) → `6 failed, 44 passed`, including both new
document-agreement tests (the third, the parse-control, does not depend on `ROW_LABELS` and stayed
green, correctly). Reverted; `diff` → identical; re-ran → 50/50 passed.

### Minor 1 — column alignment did not match the worked outputs

**Changed:** `_render_row` pads a row's label to `_LABEL_WIDTH = 19` and (for `identical`) its
verdict to `_VERDICT_WIDTH = 13` before the digest — both measured directly against
`design-principles.md`'s fenced example (`code_hash          identical    sha256:8e21...`, verdict
column at character 19 for every label length tried). `parameter_deltas` now aligns its value
column to the LONGEST changed path in a given comparison (`width = max(len(path) for path, _, _ in
changed) + 2`), matching the same document's two-line example where `parameters.analysis.method`
and the longer `parameters.analysis.min_samples` both start their values at the same column. For a
single-line batch this reduces to exactly the old fixed two-space gap, so every existing
single-delta test kept its literal-equality assertion unchanged.

**Verified by:** existing Fixture M single-line tests (`arm_one`, `arm_two`, `arm_three`, the
absent-arrow test) all still pass with exact-equality assertions unmodified; the multi-line sorted
test (which uses `.split()`, not exact equality) also unaffected. Updated the three tests that DID
assert exact fixed-spacing literals against `_render_row`'s row output (`test_h8b_fixture_r2_row_output`,
both `test_h8b_fixture_l_*` tests) to `re.search`/`re.fullmatch` on label+verdict rather than a
literal space count, since the point of those assertions was never the exact width.

### Minor 2 — M4 conflates two properties; only Fixture M's arm two isolates coverage

No code change — this is a note carried into the record, as the review asked. M4 (`_flatten(
config_a.get("parameters") or {})`) both narrows coverage AND strips the `parameters.` prefix from
every surviving path. Fixture M's arm one (metadata) is blind to both changes; arm two
(`limits.max_failed_fraction`) is what actually proves the walk lost `limits` coverage, since its
failure is "zero lines" rather than "lines with the wrong path." Recorded here so a future re-run
of M4 does not read arm two's failure as proof of a narrower claim than it supports.

### Minor 3 — reasoning-in-progress left in the committed report

**Changed:** edited the M4 mutation paragraph above (this same file) to remove the
"— no, checked again: ... see below" fragment and state the conclusion once, where the correct
explanation already lived two sentences later. This is a same-batch tidying of an unfinished
sentence, not a retro-edit of a past ruling — the report had not yet had its verdict recorded when
this round started.

### Minor 4 — with both operands unreadable, only the first was reported

**Changed:** `command_diff` now attempts both `_load_side` calls unconditionally (each in its own
`try`/`except ContractError`, appending to one shared `Collector`) before deciding whether to
refuse, rather than returning on side A's failure without ever attempting side B. An `OSError`
(a missing path) is untouched by this — it still propagates uncaught from whichever side raises it
first, since only `ContractError` is caught.

**Verified by:** `test_h8b_both_operands_unreadable_are_both_reported` (two empty directories,
both `E-UPSTREAM-RECORD-MISSING`, both paths named in the rendered output, `out.count(...) == 2`).
**Mutation, reverted:** restored the original return-on-first-failure form → `1 failed, 49 passed`;
only the new both-unreadable test failed, and every single-bad-path test (the property-preserving
arm — old and new code behave identically when only one side fails) stayed green. Reverted; `diff`
→ identical; re-ran → 50/50 passed.

### Gates after all eight findings closed

`uv run pytest` → **2609 passed, 1 skipped, 2 xfailed**. `uv run mypy` → 49 source files, clean.
`uv run ruff check .` → clean. `uv run ruff format --check .` → 88 files. Tree clean at commit time.
