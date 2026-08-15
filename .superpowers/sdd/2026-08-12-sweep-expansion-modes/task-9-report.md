# Task 9 report — consistency passes and the slice's exit criterion

Status: **DONE_WITH_CONCERNS** (two live doc-vs-code divergences found and recorded; see § Findings)

Tree checked: `h2-sweeps` @ `632018b` (final tree `24cb017`, one tests-only commit), merge-base with
`main` = `ad6cf3d` (main is an ancestor, so
`main..HEAD` is a true two-dot range here — verified with `git merge-base`).

Every check below is stated as: the command, the perturbation that proves it can fail, the result.
A pass with no firing self-test is reported as unrun.

---

## Step 0 — the three commands

| Command | Result |
|---|---|
| `uv run pytest` | 1069 passed, 0 failed (60.9 s) |
| `uv run ruff check .` | All checks passed |
| `uv run mypy` | Success: no issues found in 40 source files |

`ruff format .` deliberately **not** run (pre-existing house style across 36 files, unchanged at both
HEAD and the branch base).

## Step 1 — `groups` is still refused (behavioural, not textual)

A grep for the identifier cannot fail in the direction that matters, so the check is a config fed to
`validate` plus an assertion on `_axes`/`expand`, in a throwaway `tests/test_task9_scratch.py`
(deleted afterwards — nothing committed).

- `codes(write_config({"sweep": {"groups": [{"by": "cohort", "levels": [...]}]}}))` contains
  `E-SWEEP-GROUPS-UNSUPPORTED`. **Self-test:** rename the declared mode to `grid` in the same
  fixture → the assertion fails (`AssertionError`), proving the check reads the config rather than a
  constant. Reverted.
- `_axes(sweep) == []` and `expand(doc) == []` for a groups-only sweep: **no axis, no arms.**
  **Self-test:** add a two-line `groups` branch to `_axes` that appends one cell per level → the
  assertion fires. Reverted.
- Verified against the branch base in a scratch worktree at `ad6cf3d`: a groups-only sweep expands to
  zero conditions there too, so the empty expansion is pre-existing, not introduced here. It is
  reachable only for a config `validate` refuses fatally.
- One thing worth knowing: `AXIS_MODES` membership does **not** drive `_axes` — moving `groups` from
  `NON_AXIS_MODES` into `AXIS_MODES` changes no expansion (self-tested; the tuple is a
  classification read by `E-SWEEP-ABLATE-CROSSED` and `SWEEP_MODES`, exactly as its docstring says).
  So the tuple is not the thing to guard against a groups axis appearing; `_axes` is.
- The brief's "rows 219 and 257" are line numbers that resolve to unrelated rows at both `main` and
  HEAD (`Naming convention`, `Stratification attribute exists`), so they are stale and could not be
  used. Resolved by content instead: the § Validation rows that need a group axis
  (`Allocation needs arms`, `Every axis is assigned`, `Every assignment names an axis`,
  `Axis names are distinct`, `Arms need allocation`, `Ablation baseline isn't a group level`) are all
  still unimplemented — none of them has a registry code, and `validate.py`'s own docstring names
  "Ablation baseline isn't a group level" as the one § Validation row still open.

**`E-SWEEP-GROUPS-UNSUPPORTED` still fires. No groups axis expands.**

## Step 2 — the worked example did not move

```bash
MB=$(git merge-base main HEAD)
git diff $MB..HEAD -- README.md docs/ CLAUDE.md | grep "^-" | grep -E "0\.581|0\.607|0\.412|0\.026|−0\.007|0\.059|−0\.169|0\.014|228|240|8e21|1a2b|3d8a|6b1f|2f5c8d0"
```

No output — and the same grep over `^+` lines is also empty, so no *new* contradictory figure was
introduced either (the brief's removal-only form would not have caught that). `CLAUDE.md` added to
the path list, since it carries the canonical figures.

**Self-test:** a working-tree edit is invisible to a two-dot diff — that first attempt did **not**
fire, which is exactly the un-failable check this project keeps getting caught by. Redone as a real
temporary commit changing `0.581` → `0.582` in `reference.md`: the removal grep printed
`-          r: {value: 0.581, ...}` and the addition grep printed the `0.582` line. `git reset --hard
HEAD~1` restored `632018b`, after which both greps return 0 hits.

Expansion checked directly, not by prose: `cohort-pilot`'s sweep (`baseline:
{analysis.method: pearson}` + `grid: {analysis.method: [spearman, kendall]}`) expands to exactly
`['baseline', 'method=spearman', 'method=kendall']` with `is_baseline == [True, False, False]` —
three conditions, one baseline, byte-identical to the same call at `ad6cf3d`. **Self-test:** add a
second grid axis → the label assertion fires. Reverted.

## Step 3 — registry integrity, both directions

Authority for "documented": the two registry tables, extracted by section rather than by grep, since
a code named in prose would inflate a grep. Counts: **64 `E-` rows, 18 `W-` rows**, no duplicates —
the stated expectation, unmoved. **Self-test:** delete one row from a scratch copy → 63.

```bash
# emitted side: literal codes in src/ (verified no code is built by f-string or concatenation —
# `grep -rn 'code=f"' src/publishable` and `f"E-` are both empty, and every variable-passed code
# comes from a literal tuple in the same file, which the literal grep sees)
comm -23 src-codes.txt doc-registry.txt    # emitted but undocumented
comm -13 src-codes.txt doc-registry.txt    # documented but not emitted
```

- **Direction B (documented → emitted) is empty** against the two registry tables: every one of the
  82 documented codes is still present in `src/`.
- **Direction A**, the check that can fail: the residual set at HEAD equals the residual set at
  `ad6cf3d` **minus exactly the three retired codes** and nothing else — `diff` of the two sets shows
  only `E-SWEEP-ABLATE-UNSUPPORTED`, `E-SWEEP-PAIRED-UNSUPPORTED` and `E-SWEEP-SAMPLE-UNSUPPORTED`
  removed, no additions. The remaining residents (the surviving `-UNSUPPORTED` family,
  `E-GIT-NO-REPO`, `E-CODE-DIRTY`, `E-GIT-NO-COMMIT`, `E-INPUT-CHANGED`, `E-PROJECT-EXISTS`,
  `E-EXPERIMENT-EXISTS`, `E-EXPERIMENT-UNKNOWN`, `E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED`) are present
  identically at the base, so none is this slice's business — the brief's "only surviving
  `-UNSUPPORTED` plus `E-GIT-NO-REPO`" is narrower than the tree has ever been, which is why the
  base-vs-HEAD delta and not the absolute set is the claim made here.
- `E-SWEEP-BASELINE-PARTIAL` is gone from `src/`, `tests/`, `README.md`, all four documents — it
  survives only in `docs/superpowers/` history, marked RETIRED.
- `E-STATS-CONTRASTS-UNSUPPORTED` appears in `src/` only inside docstrings that say it *used to* be
  raised (Task 6 retired it). Not emitted, not documented. Correct.

**Self-test:** renamed `E-SWEEP-SAMPLE-INVALID` → `E-SWEEP-SAMPLE-BOGUS` in `sweep.py` and
`E-SWEEP-KEY-UNKNOWN` → `E-SWEEP-KEY-PHANTOM` in one `reference.md` row. Direction A reported
`E-SWEEP-SAMPLE-BOGUS`, direction B reported `E-SWEEP-KEY-PHANTOM`. Both reverted.

**Registry integrity holds in both directions.**

## Step 4 — the mechanical pass

Throwaway script over `README.md`, `CLAUDE.md`, the three `docs/*.md` documents and
`docs/feasibility-llm-growth-studies.md`: heading-anchor slugs (fences stripped), every relative link
and `#anchor`, duplicate anchors, table rows against their header's column count, empty rows,
trailing whitespace, tabs, invisible unicode, ASCII `x` for multiplication (fences **included**, per
`CLAUDE.md`), en dash in a heading.

**Result: 0 problems.** 669 relative links resolved (504 of them in `reference.md`), which is stated
because a zero over zero links would be the un-failable version of this check.

**Self-test:** a synthetic file carrying one of each defect produced all nine expected reports —
`DUPLICATE ANCHOR`, `BAD ANCHOR`, `MISSING FILE`, a 3-cell row under a 2-cell header, `EMPTY TABLE
ROW`, `TRAILING WHITESPACE`, `TAB`, `ASCII x FOR MULTIPLICATION`, `EN DASH IN HEADING`. The
invisible-unicode check was self-tested separately with a `U+200B` fixture (`grep -cnP` → 1).

The three named false positives needed **no** exemption: this slugger keeps `_` and `-` and strips
`.`/`&`/`—`, so `secrets--credentials`, `naming-conventions--repeat-defaults` and the
`executions.jsonl` heading all resolve on their own. Re-run with the exemption set emptied: still 0
problems. Nothing was "fixed" for them.

## Step 5 — the cross-document pass

| Class | Result |
|---|---|
| Shared worked example | Clean — Step 2 |
| Config completeness | Clean. Every field this slice made live is in § The one config file's fenced example: `sweep.paired` entries, `sweep.ablate`'s `from`/`remove`/`override`, `sweep.sample`'s `n`/`method`/`seed`/`ranges`. `sample_seed` is a `sweep.yaml` field, not a config one, and is documented as such in § `sweep.yaml` |
| Enum comments | Clean, compared against code sets rather than by eye: `# sobol \| latin_hypercube \| random` == `SAMPLE_METHODS`; `# uniform \| int_uniform \| log_uniform` == `SAMPLE_RANGE_FORMS`; the `E-SWEEP-KEY-UNKNOWN` row's six modes == `set(SWEEP_MODES)`. Every clause of the `E-SWEEP-SAMPLE-INVALID` row maps to a real branch of `sample_fault` (no `n`, `n < 1`, no/empty `ranges`, method outside the set, seed neither `auto` nor a pinned int, not exactly one range form, bounds not two ordered numbers, `log_uniform` positivity, `int_uniform` integrality) |
| Schema fields in prose | Clean |
| Declared vs derived | Clean. `sweep.sample.seed` is documented as `auto` **or** a pinned integer and `sample_seed_for` returns a pinned integer literally without computing the digest. Examined and cleared: `seed: null` is also accepted and treated as `auto` — in YAML a valueless key *is* the omitted spelling, and § What `auto` derives from already says "an omitted `seed` is `auto`, not an error", so this is not a third undocumented value |
| Versions | Clean — `CITATION.cff` 0.1.0, `reference.md`'s `publishable_version: "0.1.0"`, README's v0.x notice |
| Prevented mistakes | **Two rows re-opened by this slice — see § Findings.** The rest hold: "A typo'd parameter silently using a default" now covers `sample.ranges` keys via the widened `E-SWEEP-PATH-UNKNOWN`; no new mode lets a roster-changing variant become an axis (`sample`/`paired`/`ablate` all write parameter paths only, and `data.units` is untouched by expansion) |

### The Task-7 class, checked deliberately

Task 7's defect was editing a document to describe behaviour the code did not have, so every sentence
Tasks 7 and 8 added was matched to the function that makes it true.

- § Expansion modes row 2 verified by running it: a baseline fixing `analysis.method` over a grid
  sweeping `analysis.method` and `data.sex` produces `sex=f__baseline`, `sex=m__baseline`,
  `method=spearman__sex=f`, … and `baseline_for` targets `method=spearman__sex=f` →
  `sex=f__baseline`, `method=kendall__sex=m` → `sex=m__baseline`; `resolve_contrasts` yields exactly
  `[(2,0), (3,1), (4,0), (5,1)]`. The row's labels and its "matching the free axes' values rather
  than by position" are both literally what the code does.
- The closing "every contrast differs in exactly one place" is scoped by its own antecedent (fix *the
  factor* you are measuring, leave the stratifying axes free) and is true under it. Measured the
  neighbouring shape too — a baseline fixing **two** of three axes leaves contrasts differing on both
  — and that is already recorded, ruled on, and pinned by
  `test_a_partly_fixed_baseline_is_silent_while_its_run_marks_confounded`. No new gap.
- The `W-SWEEP-BASELINE-CONFOUNDED` remedy in the code ("fix the axis you are measuring and leave the
  ones you are stratifying over free, and each cell gets its own baseline") matches the remedy the
  document and `spec-defects.md` scoped, word for word in substance. The row's "only for a baseline
  that fixes every one of them" matches the code's guard.
- The two routed open questions (per-cell baseline numbering; row 2's ordering) were left alone.

---

## Findings

Two live doc-vs-code divergences, both created by this slice's own sequencing: Task 3 verified that
`sample`'s two "not a family" claims held **structurally, because `baseline` + `sample` was refused
by `E-SWEEP-BASELINE-PARTIAL`** (its progress note says exactly that: "`resolve_contrasts` needs a
DECLARED baseline and a sample-only sweep has none"). Task 6 then retired that refusal and made
`baseline` + `sample` a legal per-cell design — which removed the protection nobody re-checked.

Both are recorded in `docs/superpowers/spec-defects.md`; the documents were **not** edited, because
in both the document is the thing that is right.

1. **A sampled condition joins the correction family.** `reference.md` § Sweeps and repeats: "`family`
   counts conditions from `grid`, `paired`, `ablate`, and `groups`, and skips `sample`", and
   § Validation's row: W-STATS-FAMILY is "Not raised for a `sample`-only sweep, whose draws aren't a
   family". **Two code sites, named separately in the entry because a fix at one leaves the other
   live:** `validate`'s `comparisons = len(resolve_contrasts(doc, conditions))`, and `cli.py`'s
   `vs_baseline_members + contrast_members`, which carries no mode filter at all.
   - Repro (a), `baseline` + `sample` — and `baseline` is a non-axis mode, so this *is* the
     "sample-only sweep" § Validation exempts: validates with no `E-`, `resolve_contrasts` → 3
     comparisons, `validate` reports exactly `{W-STATS-FAMILY}` under `correction: none`.
   - Repro (b), `grid × sample`, which breaks the § Sweeps and repeats claim under any reading of
     "sample-only": 9 conditions, **6** comparisons where counting grid and skipping sample gives
     **2**, no error and no warning (the default `holm` corrects all six at α/6 … α).
   - The sentence's other half — "`report` says so beside the table" — is dormant, not violated:
     this build has no `report` command (`validate`, `run`, `new`, `generate`/`init` only).

2. **A sampled condition's label is a float, not `NN_sample`.** § How artifacts are organized:
   "Sampled conditions are labelled `01_sample`, `02_sample`, with the drawn values in `sweep.yaml`
   and in `results.conditions[i].values`", with the reason attached (a draw "has no short exact
   spelling", and a selector must name "a discrete label, never a float you have to spell identically
   twice"). At HEAD `label_for` renders the drawn value like every other axis, so the labels are
   `confidence=0.8615282253183009` and the condition directories are
   `01_confidence=0.8615282253183009`. Nothing in `sweep.py`, `artifacts.py` or `runner.py` produces
   a `NN_sample` label. The entry records **why this is not a one-line change to `label_for`**: under
   the documented rule every draw's label *body* is the literal `sample`, while a selector "names the
   label's body rather than its prefix" and `_condition_labels` returns a **set** — so n draws would
   share one body and collapse there. That is a ruling about selector identity for a later slice, and
   the entry routes it as one rather than as a rendering tweak.

The two compound: a declared `statistics.contrasts` entry is the one way a sample condition joins the
family without a baseline, and declaring one today means typing `confidence=0.8615282253183009` by
hand.

Neither is a `groups` regression and neither moves a worked-example figure. Neither blocks: the one
blocking defect the brief names is a `groups` axis expanding, and Step 1 shows behaviourally that
none does.

## Triage of Task 2's end-of-slice request

`progress.md` addressed one item to the final task: "the paired value-checking gap names owner H2 …
worth triaging at the end rather than assuming a later task picks it up." **Still open at HEAD**,
verified rather than assumed — each of these validates with **zero** findings:

- `sweep.paired: [{analysis.min_sample: 30}]` (a typo of `min_samples`) — no `E-SWEEP-PATH-UNKNOWN`
- `sweep.paired: [{analysis.method: pearsonn}]` — no `E-PARAM-VALUE`
- `sweep.paired: [{analysis.method: "a long sentence"}]` — no `E-SWEEP-VALUE-UNNAMEABLE`

`_check_sweep` runs `_path_resolves`/`_value_checks` over `grid`, `sample.ranges` and `ablate`'s
`override`; `paired` gets only the `_check_shape` guards and `E-SWEEP-PATH-DUPLICATE`. Owner is still
H2 with no task claiming it, exactly as Task 2 said — it needs a charter revision or a new task, and
Task 9 is not the place to mint three checks without a brief. Not fixed here; flagged for the final
review.

## Commits

**One, tests only: `24cb017` — "test: pin the two sample claims task 6 left unprotected".**

The four documents and `CLAUDE.md` came back clean from both passes, so no `docs:` commit was made and
no empty commit created. What the commit carries is the two findings' tracked handles: the entries
went to `docs/superpowers/spec-defects.md`, which `.gitignore:224` excludes (`docs/superpowers/`), and
`.superpowers/` is ignored too — so both natural carriers are working-tree-only and would not survive
the merge, which is the lost-finding failure Task 2 already flagged once. Each finding therefore also
gets an `xfail(strict=True)` test asserting the *documented* behaviour:
`test_a_sampled_condition_is_labelled_sample_not_by_its_drawn_value` (`tests/test_sweep.py`) and
`test_sample_draws_are_not_comparisons_in_the_correction_family` (`tests/test_contrasts.py`). The
suite stays green and the marker cannot survive the fix. **Self-test:** replacing one of the two
assertions with a passing one turns the run into `XPASS(strict)` → `FAILED`, so the markers are load
bearing rather than decorative. Reverted.

The throwaway `tests/test_task9_scratch.py` used for the behavioural checks was deleted; `git status`
is clean apart from the ignored paths.

## The slice's exit criterion

- `E-SWEEP-GROUPS-UNSUPPORTED` **still fires**, and no `groups` axis expands (behavioural check, both
  directions self-tested).
- **No worked-example figure moved** — no removal and no addition matches the canonical set, proven
  with a firing self-test over a real temporary commit.
- **Registry integrity holds in both directions** — every documented code is emitted; the emitted
  residual is the base set minus exactly the three retired codes.
- On the final tree at `24cb017`: `uv run pytest` **1069 passed, 2 xfailed**, `uv run ruff check .`
  **All checks passed**, `uv run mypy` **Success: no issues found in 40 source files**. (The two
  xfails are this task's own strict handles for the findings above; the pre-existing count of 1069
  passing is unchanged.)

---

# Fix round 1 — `E-SWEEP-SAMPLE-BASELINE`

Commit **`012472d`** — "fix: refuse a baseline beside a sample axis until the family excludes draws".
Separate from `24cb017`, as directed. Final tree: `012472d`.

**Ruling implemented as given:** the family semantics were *not* implemented; the protection Task 6
removed was restored narrowly as a validate-time refusal of `sweep.baseline` declared beside
`sweep.sample`, in the same specified-but-not-implemented idiom, and placed in `_check_unimplemented`
— the function `E-SWEEP-BASELINE-PARTIAL` itself lived in (verified against `ad6cf3d`).

**One deviation, flagged rather than taken silently: the code is named `E-SWEEP-SAMPLE-BASELINE`, not
`…-UNSUPPORTED`.** § The one config file says of the `-UNSUPPORTED` family: "That whole family is
deliberately absent from the validate-time registry … which is why this list, and not that table, is
where a refused block is named." An `-UNSUPPORTED` code carrying a registry row would contradict that
sentence, and requirement 1 asks for the row. The precedent the ruling itself cites resolves it:
`E-SWEEP-BASELINE-PARTIAL` was *not* named `-UNSUPPORTED`, *did* carry a registry row, and *did* use
the "specified but not implemented in this build" message idiom. This follows it exactly — the idiom
is in the message, not the identifier. Also: the "Eleven declarations … marked `NOT BUILT`" count in
§ The one config file is **unchanged**, because this refuses a *combination*, not a declaration —
`sweep.sample` remains built and unmarked, exactly as `E-SWEEP-ABLATE-CROSSED` refuses a composition
without `ablate` being NOT BUILT.

### 1. Registry rows — the count moved 64 → 65 by this fix, not by drift

- `reference.md` § Validation → `### Errors validate reports` gains one row for
  `E-SWEEP-SAMPLE-BASELINE`, placed in the table's existing alphabetical position (before
  `E-SWEEP-SAMPLE-INVALID`). **`E-` rows: 65. `W-` rows: 18, unmoved.**
- The § Validation table (the check-by-mistake table, which is separate) gains
  **"Sample draws aren't compared to a baseline"**, beside the two existing `sample` rows.
- Both registry directions re-run: direction B (documented → emitted) still empty; direction A gains
  nothing — the new code is documented. Mechanical pass over all six files re-run: **0 problems**
  (table-column counts included, which is what a two-cell row in a two-column table needs).
- Worked-example grep re-run over the full working diff (`^-` and `^+`): 0 hits.

### 2. The strict xfail's reason line, rewritten

`tests/test_contrasts.py::test_sample_draws_are_not_comparisons_in_the_correction_family` keeps its
`expand`/`resolve_contrasts` level — that is where the semantics will land — and its reason now says
the refusal is the *current* protection, that no config reaches the inflated family today, and that
the owner is the slice owning the correction family, which lands the exclusion and retires the
refusal together. Its docstring also records the arithmetic that makes the full fix not-here: the
document's expected count is **2, not 0**, so the draws collapse into the grid's comparisons rather
than being dropped as subjects, and a skip-filter would ship a second wrong number under this same
assertion. The `spec-defects.md` entry got the same treatment, including "shipped instead, and
narrowly" with the retirement condition.

### 3. Tested both ways, and mutation-tested

| Test | Asserts |
|---|---|
| `test_a_baseline_beside_a_sampled_axis_is_refused` | `codes(path) == {"E-SWEEP-SAMPLE-BASELINE"}` — exact set, so nothing else fires. Its `expand` assertions are kept unchanged, since `expand` is not what moved |
| `test_a_sample_sweep_with_no_baseline_stays_legal` | no findings at all, and still expands to 4 conditions |
| `test_a_declared_contrast_over_a_sample_sweep_stays_legal` | a declared `statistics.contrasts` entry over two drawn labels reports no `E-` |
| `test_a_baseline_beside_a_grid_is_untouched_by_the_sample_refusal` | `codes(...) == set()` for the ordinary enumerated design |

The rewritten first test replaces `test_a_baseline_that_leaves_a_sampled_axis_free_doubles_the_draws`,
which pinned the doubling "as the behaviour that ships, not as the behaviour that is wanted" and said
"if a later slice warns or refuses, this test is where the decision lands". It lands there, and the
docstring says so.

**Mutation test — three mutants, each killed:**

| Mutant | Result |
|---|---|
| Guard replaced by `if False:` (refusal deleted) | `test_a_baseline_beside_a_sampled_axis_is_refused` FAILED |
| Guard widened to `if sweep.get("sample"):` (baseline half dropped) | both "stays legal" tests FAILED — the refusal-wider-than-the-harm case is pinned |
| Guard narrowed with `and False` | `test_a_baseline_beside_a_sampled_axis_is_refused` FAILED |

### 4. Revert verified by behaviour, with `__pycache__` cleared

`find . -name __pycache__ -type d -prune -exec rm -rf {} +` was run **between every mutation and the
next**, not only at the end — the same-size, same-second `.pyc` staleness Task 8's reviewer
established would otherwise make a revert invisible permanently. After the final revert the guard was
re-read from source, the file re-parsed, and the four tests re-run green; then the whole suite.

### Green on `012472d`

`uv run pytest` **1072 passed, 2 xfailed** (the three new tests plus the rewritten one; 1069 → 1072),
`uv run ruff check .` **All checks passed**, `uv run mypy` **Success: no issues found in 40 source
files**.

### Left alone, as directed

Finding 2 (sampled labels rendering drawn values) — untouched, its `xfail(strict=True)` unchanged
apart from nothing. The `sweep.paired` per-entry value gap — untouched, still routed with its owner.
The two routed open document questions — untouched.

### Two reachability checks the refusal could have broken — both clean

A validate-time refusal can quietly turn an existing test into a test of an unreachable state, and a
green suite does not distinguish the two. Checked by reading the configs, not by the exit code:

- **Task 3's fix for the run/summary unreadable-path set** (`_swept_paths(sweep) | baseline`) is
  pinned by `tests/test_cli.py::test_a_sampled_path_is_unreadable_at_run_scope`, whose sweep declares
  `sample` **and no baseline** — so it still goes through `validate` and a real `run`, and still
  exercises the sampled-path branch. Unaffected. Its `ablate` sibling declares `baseline` + `ablate`
  and no `sample`, also unaffected. Both re-run green on their own.
- **`E-SWEEP-PATH-DUPLICATE`'s reach is not narrowed.** Its `grid` ∩ `sample` test declares no
  baseline, so the case its rationale calls the worst — `sweep.yaml` recording the drawn value while
  the run used the grid cell's — stays reachable and refused. The new row is about a `baseline`
  combination and says nothing about path sharing.
- The three adjacent § Validation rows were read in rendered order (`Sample ranges`, the new
  `Sample draws aren't compared to a baseline`, `Sample is drawable`): the new row names the error's
  condition only, and `W-SWEEP-BASELINE-CONFOUNDED` lives in the separate § Warnings table, so there
  is no path for a reader to conflate the two.
