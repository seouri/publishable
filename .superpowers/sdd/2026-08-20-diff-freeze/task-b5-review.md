# Batch 5 review — tasks 7, 8 (`covered_config`'s delta walk; `diff.py`'s form detection, header, four rows)

Reviewed 2026-08-20 against `9b7dec0` on branch `h8b-diff-freeze`. Commits under review: `986f10a`
(task 7), `ed615e4` (task 8), `9b7dec0` (report). Every mutation was applied to a saved copy,
reverted by editing back, and the revert verified by `diff` against the copy **and** by re-running
the targeted tests green. **The tree is clean** — `git status --short` empty at the end.

## Verdicts

Graded on the scale `task-b4-review.md` used at review time — *PASS with findings*, findings to be
closed in a fix round before the ledger records a verdict. Batch 4 carried three Majors under that
wording, one of them a carried finding the report claimed closed and had not built; nothing here is
worse than that, so a FAIL would be a scale change rather than a judgement, and I am not making one
silently.

- **Spec compliance: PASS with findings.** Decisions 1, 4, 5 (parts 1–3) and 6's header are
  implemented as written, and Decision 3's extraction is genuine — one projection, two readers, no
  second list, verified by narrowing the projection and watching both readers move. Where it
  diverges is Decision 3's own stated invariant, *"the verdict above these lines and the lines
  themselves cannot disagree about coverage"*: `_flatten` drops an empty mapping, so the row prints
  `DIFFERS` with no delta lines over a pair `publishable init`'s own output produces (Major 1). One
  further divergence from the three worked outputs the design derives the rows from: scalar deltas
  render as Python reprs rather than as the config's own YAML (Major 3).
- **Task quality: PASS with findings.** Four Majors, four Minors. Two of the Majors are unpinned
  specified behaviour — the one-sided `not captured` arm, disclosed but mis-owned to task 10, and
  task 8 step 4's document-derived label pin, which was **not built and not disclosed as unbuilt**
  (batch 4 graded an unpinned Decision-10 warning a Major on the same reasoning). Credit where due:
  the extraction is a real extraction, arm G holds, every prescribed mutation was genuinely run, and
  the report's account of each one matched what I reproduced — including its own correction of a
  first-skim reading of M4's failure.

## Gates, run directly at clean HEAD

| Gate | Result | Expected |
|---|---|---|
| `uv run pytest` | **2600 passed, 1 skipped, 2 xfailed** (167.21 s) | 2600 / 1 / 2 ✓ |
| `uv run ruff check .` | All checks passed! | ✓ |
| `uv run ruff format --check .` | **88 files** already formatted | 88 ✓ |
| `uv run mypy` | Success, **49 source files** | 49 ✓ |

---

## Findings

### Major 1 — `_flatten` drops an empty mapping, so `parameters_hash DIFFERS` prints with **zero** delta lines, over a pair `init`'s own output produces

**File:** `src/publishable/diff.py:122-135` (`_flatten`), reached from `parameter_deltas`
(`:146-161`) and `_render_row` (`:200-202`).

`_flatten` recurses on `isinstance(value, dict)` and stores only non-dict leaves, so an **empty
dict contributes no leaf at all**. `covered_config({"sweep": {}})` and `covered_config({})` flatten
to the same `{}` — while `parameters_hash` over the two canonical JSON payloads differs. The row
therefore prints `DIFFERS` and nothing under it: exactly Decision 3's cost-if-wrong, *"the reader's
conclusion would be that something changed that core cannot name"*, in the batch whose entire
purpose is that the two readers of one projection cannot disagree.

**Verified by running**, in three steps:

1. Pure-function probe: `parameter_deltas({'a': {}}, {})` → `[]` while
   `parameters_hash` differs. Same for `({'data': {'units': {}}}, {'data': {}})` and
   `({'statistics': {}}, {})`.
2. Reachability from shipped code: scaffolded a project and ran
   `publishable init myexp --template generic --input-dir … --output-dir …`. The materialized
   `config.yaml` contains **`sweep: {}`**, whose own inline comment reads *"Empty (or omitted) means
   a single, unswept condition"* — the two spellings are declared equivalent by the file `init`
   writes.
3. End to end on that real config: with `b = deepcopy(a); del b['sweep']`,
   `parameters_hash(a) != parameters_hash(b)` is `True`, `parameter_deltas(a, b)` is `[]`, and
   `_render_row('parameters_hash', …)` returns exactly `['parameters_hash    DIFFERS']`.

So a user who deletes an empty `sweep:` block between two runs — a no-op the config file tells them
is a no-op — gets `DIFFERS` with no explanation. The fix is a one-line rule in `_flatten` (emit an
empty `dict` as a leaf, rendering `{}` through `_render_leaf`'s existing YAML-flow branch); it needs
a Fixture M arm to pin it, and the arm must assert the **line count**, since the verdict is
`DIFFERS` under both branches.

**The projection itself manufactures an empty mapping**, which locates the defect precisely in the
seam between the two readers rather than in user input: `covered_config({"data": {"input_dir": "/x"}})`
returns `{"data": {}}` — verified by running — an empty dict present in neither operand, produced by
the narrowing. Against a config with no `data` key at all, the hashes differ and `_flatten` yields
nothing on either side. That particular pair is theoretical, since the schema requires `data.units`,
but it means the projection and the walk disagree **by construction**, not only on an input shape
nobody guarded.

Two more things to carry with it, neither a separate finding:

- **A second, narrower route to the same shape.** `_flatten` joins with `.`, and `sweep.grid`'s keys
  are themselves dotted, so `{'a': {'b': 1}}` and `{'a.b': 1}` flatten identically. Verified by
  running: hash differs, deltas `[]`. Far less reachable than the empty-dict route, but the same
  ambiguity in the same function.
- **`spec-defects.md` already documents this flattening blindness**, in the OPEN entry
  *"`declared_credential_names` reports a template-default credential for a parameter value never
  written"*, which states the mechanism verbatim (*"recurses into every nested `dict` and only ever
  stores leaf, non-dict values"*) and whose owner clause reads *"whichever slice next touches
  `_flatten_parameters`/`_flatten`"*. That entry is about `cli._flatten_parameters`, not this new
  function, so it was not violated — but the mechanism was on file and this batch built a second
  `_flatten` with the same blind spot and a more consequential effect.

### Major 2 — the one-sided arm of the `not captured` guard is entirely unpinned, and its failure mode is a crash

**File:** `src/publishable/diff.py:196` (`if figure_a is None or figure_b is None:`).

Behaviour at HEAD is **correct** — verified by running `_render_row('uv.lock', …)` over a non-null
side against a null side in both orders, and both return `['uv.lock    not captured']`. What is
missing is the pin.

**Verified by running the narrow mutation** the report did not run: `or` → `and`. Two-null still
returns `not captured` (both `None` satisfies `and`), so every committed fixture stays green. **Full
suite under the mutant: 2600 passed, 1 skipped, 2 xfailed** — identical to HEAD. The guard's
one-sided arm is invisible to the entire suite. Under the same mutant, the one-sided case raises
`AttributeError: 'NoneType' object has no attribute 'partition'` out of `_truncated` — verified by
running — so the unpinned behaviour is a **crash out of the command**, not a cosmetic verdict.

M1 as prescribed (remove the whole guard) is caught, because both-null is what Fixture R2 exercises;
it does not discriminate the `or`. The report's own "Concerns for the next batch" flags the missing
one-sided arm and proposes deferring it to task 10.

**On the review prompt's question — close now, not at task 10.** Three reasons. The material already
exists in this batch (Fixture L's non-null `run_a` against any `run_a_project` scaffold's null run —
the report says it built exactly that pair by hand). Task 10 owns the **config side's** `not
comparable` vocabulary, a different code path and a different word; parking a run-vs-run guard's pin
there mis-owns it and is how a carried finding falls out of the chain, which the ledger records
happening twice on this branch already. And the exposure is a crash, which is above the bar this
repo defers.

### Major 3 — `_render_leaf` prints Python reprs where the config speaks YAML, so a delta line names a value that is not in either file

**File:** `src/publishable/diff.py:138-143` (`_render_leaf`).

Only `dict` and `list` leaves are routed through `yaml.safe_dump`; every scalar takes `str(value)`.
So a boolean renders `True`/`False` and a null renders `None`, against config files that say `true`,
`false` and `null`.

**Verified by running**, on the pure function:
`parameter_deltas({'parameters': {'a': True}}, {'parameters': {'a': False}})` →
`['  parameters.a  True → False']`, and
`parameter_deltas({'data': {'units': {'cluster_by': None}}}, {'data': {'units': {'cluster_by': 'site'}}})`
→ `['  data.units.cluster_by  None → site']`.

Reachable from `init`'s output in a single edit: the config I scaffolded carries
`drop_missing: true` under `parameters.analysis` and four `null`s under `data.units`
(`cluster_by`, `weight_by`, `measurements`, `holdout`). A reader who greps their own config for
`True` or `None` — the strings `diff` just printed at them — finds nothing. The design's whole
argument for the delta walk is that *"a truncated delta is a delta a reader cannot act on"*; a delta
in the wrong language is the same objection.

Fix is in the same function as Major 1's and belongs in the same round: route scalars through
`safe_dump` too (`yaml.safe_dump(True).strip()` is `'true'`), or special-case `bool` and `None`.
Note that a `str` scalar must keep `str(value)` rather than gaining YAML quoting, so this is not a
one-line widening of the existing branch.

### Major 4 — task 8 step 4's document-derived label pin was not built, and the report presents a pre-writing grep as though it discharged the step

**File:** `tests/test_diff.py` (absent).

The brief is explicit: *"**Pin the labels against the DOCUMENTS' text, not against your own
constant**"*, and it names the in-repo shape (`_status_tables`/`_interval_method_names` in
`tests/test_cli.py` — parse the document, assert against what it says). **Verified by grep**: no test
in `tests/` opens `README.md`, `docs/design-principles.md` or `docs/reference.md` to derive the row
labels; the only files in `tests/` naming those documents are `test_templates.py`, `test_validate.py`
and `test_scaffold.py`, none of them about `diff`. If `reference.md` renamed `uv.lock` to
`uv_lock_hash` tomorrow, nothing fails.

What the report offers in its place, under "What was grepped", is a grep run **before** typing
`ROW_LABELS` — that is the implementer's own reading, not a pin, and the section presents it as the
step's discharge. The labels themselves are correct: I re-ran the grep over the three named files and
all three worked outputs spell `input_manifest` and `uv.lock`, never the `_hash` forms. The defect is
the missing pin and the undisclosed omission, not the labels.

### Minor 1 — the emitted rendering does not reproduce the three worked outputs' column alignment, and no task owns reconciling it

**File:** `src/publishable/diff.py:197-203`, `:160`.

All three worked outputs pad the label to a common column (`code_hash          identical    sha256:8e21…`,
label width 19). `_render_row` emits a fixed four-space separator (`code_hash    identical    sha256:8e21…`),
and `parameter_deltas` emits a fixed two-space separator where the documents align the value column.
**Verified by reading** README.md:271-276, docs/design-principles.md:118-124 and
docs/reference.md:3133-3139 beside the emitted strings.

Nothing in Decision 1 makes alignment normative, and `_truncated`'s docstring claim (*"the width all
three worked outputs show"*) is about the **digest** and is true — verified, all three show four hex
characters. But a reader who copies a line out of README to grep for it will not find it, and task
12's document work is scoped to the `...` → `…` fix. Flagging so it is a decision rather than a
drift.

### Minor 2 — M4 changes two properties at once, and only Fixture M arm two isolates the one it is named for

**File:** the mutation prescribed in task 7 step 5, applied at `src/publishable/diff.py:152-153`.

**Verified by running**: applied M4 exactly as the report describes → **5 failed, 36 passed** in
`tests/test_diff.py tests/test_hashes.py`, with Fixture M arm one (metadata) among the passes. The
report's claim about the property-preserving arm is confirmed.

The conflation: M4 replaces `_flatten(covered_config(config_a))` with
`_flatten(config_a.get("parameters") or {})`, which narrows coverage **and** strips the
`parameters.` root from every emitted path. Fixture R2 fails on the second property, not the first —
its filter matches zero lines because the path became `analysis.min_samples`. The report catches this
and says so, which is good; the residue is that the mutation as prescribed does not cleanly
discriminate coverage, and only arm two does. Worth carrying into any re-run of M4.

I also re-ran the second prescribed mutation (list-as-subtree, task 7 step 6): **2 failed, 39
passed**, failing the reordered-list arm and the absent-arrow test, matching the report exactly. And
I ran the review prompt's own prescription — **narrow `covered_config` itself** (drop `limits` from
the projection): **3 failed**, one on each side of the seam —
`test_h8b_arm_g_max_failed_fraction_change_differs` (the hash reader) and
`test_h8b_fixture_m_arm_two_limits_only_edit_is_exactly_one_line` (the delta reader), plus the
projection test. **Both readers move together, and Fixture M's pair is genuinely what discriminates**:
arm one passed under every narrowing arm I applied.

### Minor 3 — the committed report contains unresolved reasoning-in-progress

**File:** `.superpowers/sdd/2026-08-20-diff-freeze/task-b5-report.md`, the M4 bullet.

*"…so it happened to still work for the wrong reason there — no, checked again: `min_samples` IS
under `parameters`, so that failure came from a different assertion in the same test; see below"*.
The correct answer is given two paragraphs later, but a tracked record should carry the conclusion,
not the route to it. The ledger's own standard from the last batch — *a claim broader than its
evidence* — has a sibling here: a claim narrower than the author's own subsequent correction, left
in place.

### Minor 4 — with both operands unreadable, only the first is reported

**File:** `src/publishable/diff.py:214-225`.

`command_diff` loads side A, returns on its `ContractError`, and never reaches side B. **Verified by
running** `command_diff(Path('e1'), Path('e2'))` over two empty directories: one
`E-UPSTREAM-RECORD-MISSING` for `e1`, `1 problem`, exit 1. A user with two bad paths fixes one,
re-runs, and learns about the second.

`command_diff` is not `validate` and the *collect rather than abort* invariant is stated for
`validate`, so this is not a rule violation — but a `Collector` is already in scope, both loads are
independent, and Decision 4's exit-`1` ruling is unaffected either way. Task 10 owns the exit-code
ruling and is the natural home.

---

## Attack list — what was checked and how

| # | Item | Verdict | Verified by |
|---|---|---|---|
| 1 | `parameters_hash` **calls** `covered_config`; no second projection; both readers move together | **PASS**, but see Majors 1 and 3 | **Running.** `grep -rn 'input_dir\|output_dir\|"metadata"'` over `hashes.py`/`diff.py` → the exclusion set is built in exactly one place, `covered_config`. Narrowed the projection (dropped `limits`) → a hash-side test and a delta-side test both fail. Reproduced both Fixture M arms; arm one passes under every narrowing, arm two fails — the pair is genuinely required |
| 2 | `not captured` reproduces the measured live failure; the one-sided case | **FAIL** — Major 2 | **Running.** HEAD returns `not captured` for both one-sided orders; the `or`→`and` mutation leaves the **full suite at 2600 passed** and turns the one-sided case into an `AttributeError` crash |
| 3 | Shipped `test_hashes.py` tests unchanged; same digest before and after | **PASS** | **Running.** `git diff d25f141..HEAD -- tests/test_hashes.py \| grep '^-'` → one removed line, the import. Extracted `d25f141`'s `hashes.py` to the scratchpad and compared digests against HEAD's over ten configs covering every branch of the old inline projection (`data` absent, `data` null/str/list, `metadata` absent, `data` reducing to `{}`, empty config, nested, `sweep: {}`) — **0 mismatches** |
| 4 | Row order pinned against a literal, not the constant | **PASS** | **Running.** Reversed `ROW_LABELS` **and** commented out line 371's redundant `assert ROW_LABELS == [...]`; the output-based assertion at line 387 fails on its own. `_row_labels_in_output` loops output lines outer and `ROW_LABELS` inner, so the extracted sequence follows output order and moves with the mutation while the literal does not. Restored both, verified by `diff` against the saved copies |
| 5 | Correction 5 — normalization not implemented, not claimed, filing cited not restated or struck; `(absent) → <default>` surfaced not owned | **PASS** | **Running + reading.** `git diff d25f141..HEAD --stat` shows `spec-defects.md` untouched; the entry *"`parameters_hash` does not normalize to what `init` would have materialized"* is present, OPEN, owner H6, unstruck. `covered_config`'s docstring cites it **by its own title** and restates none of its content. No normalization code, and no fixture arm for the `(absent) → <default>` consequence anywhere in `tests/` |
| 6 | Correction 3 — `OPERATION_COMMANDS`' quoted literal deleted, claim kept | **PASS** | **Running.** `grep -rn 'OPERATION_COMMANDS' src/ docs/ tests/` → only the definition (`{"validate", "run", "freeze"}`) and its one use in `cli.py`. `artifacts.py:270` now reads *"`cli.py` has no `resume` command yet"* and `reference.md:1217` *"`cli.py` has no `resume` command"* — literal gone from both, claim intact, not rewritten to a new literal |
| 7 | Mutation quality — property-preserving arm checked for each | **PASS with Minor 3** | **Running.** M4: 5 failed / 36 passed, arm one passes. List-as-subtree: 2 failed / 39 passed, scalar and sorted arms pass. Row order: 1 failed. No mutation had both arms failing the same test the same way. The conflation in M4 is Minor 2 |
| 8 | Prose and pins — no § Errors rows, no counts, no positional locators, `×`, no config-count claim | **PASS with Minor 1** | **Running + reading.** `grep -rn 'E-DIFF-CONFIG-UNREADABLE'` over the four documents → **zero hits**, so task 12's rows are untaken. `diff --stat` shows `tests/test_hashes.py` gained only new arms — task 13's guard pins are untouched. No table-row positional locators; the two `above`/`below` phrases refer to printed output lines and to a literal in the same statement. `grep -n '[0-9] *x *[0-9]'` over the three files → zero hits, so no `x`-for-`×` (there is no multiplication in this batch's prose). No config-count claim and no fifth number anywhere in the batch. The count phrases in `diff.py` (*"the four rows"*) are scoped to this task and name task 9 as the editor, which is the self-maintaining form |
| — | **Nothing dispatches** | **PASS** | **Running.** `main(["diff", "a", "b"])` → *"`publishable diff` is specified but not built in this version"*, exit **2**. `grep -rn 'command_diff\|publishable.diff'` over `src/` → hits only inside `diff.py` itself; `cli.py`'s only `"diff"` occurrence is its `NOT_BUILT_COMMANDS` entry at line 148 |

## What I could not check

- **Whether a fix for Major 1 leaves every existing hash undisturbed.** The fix is in `_flatten`, not
  `covered_config`, so on reading it cannot move a digest — but I did not build the fix, so that is
  read rather than run.
- **The alternative naive-implementation variant the report names** — formatting a raw `None` hash
  without `_truncated`, producing a false `DIFFERS sha256:None… → sha256:8e21…`. The report says it
  was not separately re-verified; I did not verify it either, because the `or`→`and` result (Major 2)
  already settles that the arm is unpinned regardless of which naive form a regression takes.
- **Task 9's insertion of `'apparatus'` into `ROW_LABELS`.** The one-authorized-editor clause is
  present at `diff.py:29-33` and `tests/test_diff.py:352-357` and names task 9 and the exact
  post-edit position; whether task 9 honours it is next batch's review.
