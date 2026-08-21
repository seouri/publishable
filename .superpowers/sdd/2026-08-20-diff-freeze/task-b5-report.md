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
  the real-run Fixture R2 test (`min_samples` lives under `parameters`, so it happened to still
  work for the wrong reason there — no, checked again: `min_samples` IS under `parameters`, so
  that failure came from a different assertion in the same test; see below).
- Reverted by editing `diff.py`'s two lines back; `diff /tmp/diff.py.orig src/publishable/diff.py`
  → **identical**; re-ran `tests/test_diff.py tests/test_hashes.py` → **41 passed**.

Fixture R2's own row-output test also failed under M4, and it is worth being precise about why,
since `min_samples` genuinely lives under `parameters` and the mutation still sees a value there.
Read the failure text rather than trusting the pass/fail count: `M4`'s mutation is
`flat_a = _flatten(config_a.get("parameters") or {})` — it flattens the **`parameters` sub-dict
directly, with no prefix**, so the emitted path becomes `analysis.min_samples`, not
`parameters.analysis.min_samples`. The test's own filter
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
  one. This is in scope for task 10's "not comparable" work or could be added earlier; flagging
  rather than silently deferring.
