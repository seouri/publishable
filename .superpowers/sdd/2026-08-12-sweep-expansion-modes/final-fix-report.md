# Final fix report — whole-branch review of `h2-sweeps`

Base `82dff37`. Four commits, all five items fixed as described. No item was declined.

`uv run pytest`: **1079 passed, 2 xfailed** (was 1072 + 2; +7 new tests).
`uv run ruff check .` and `uv run mypy` both green. `ruff format` deliberately not run.

| Commit | Item |
|---|---|
| `884959a` | Critical — `sweep.paired`'s four value-level checks, the two `reference.md` registry rows, six tests |
| `39477bf` | Important — `W-SWEEP-BASELINE-CONFOUNDED`'s truth condition, in the row and at the emit site, plus one test |
| `2023358` | The three stale claims |
| `7fb6bb7` | A follow-up on `39477bf`'s own new comment (see below), and this report |

---

## Critical — `sweep.paired` gets the four checks (`884959a`)

**The fix.** A loop over `sweep.paired` entries in `_check_sweep`, placed between the
`grid` loop and the `sample` block so source order matches `_axes` order, calling
`_path_resolves` then `_value_checks(..., nameable=True)`. No new identifiers.

**Shape ordering confirmed, guarded anyway.** `_check_shape` refuses a non-list `paired`,
a non-mapping entry and a non-string key with `E-CONFIG-SHAPE` and returns `ok = False`;
`validate_config` returns at `if not _check_shape(doc, c)` before `_check_sweep` runs. So
the loop is unreachable with a shape it would crash on. Both `isinstance` guards are kept
regardless, mirroring the `ablate.override` loop's own `continue  # _check_shape already
refused it, fatally` — `_check_sweep` is called directly by tests, and `validate` collects
findings and never raises.

**Measured, before and after.** Command: a throwaway `tests/` probe printing every `E-`
code from `validate_config`, deleted before commit.

| `paired` | at `82dff37` | after |
|---|---|---|
| `[{analysis.methdo: x}]` | *(none)* | `E-SWEEP-PATH-UNKNOWN` |
| `[{analysis.method: pearsonn}]` | *(none)* | `E-PARAM-VALUE` |
| `[{analysis.min_samples: "thirty"}]` | *(none)* | `E-PARAM-VALUE` |
| `[{analysis.method: "a/b"}]` | *(none)* | `E-PARAM-VALUE`, `E-SWEEP-VALUE-UNNAMEABLE` |
| `[{analysis.method: ["a","b"]}]` | *(none)* | `E-PARAM-VALUE`, `E-SWEEP-VALUE-UNNAMEABLE` |

The path-traversal case is pinned by its own test,
`test_a_paired_value_containing_a_path_separator_is_refused`, on `a/b` — the minimal form
of `00_method=../../evil`.

**Tests: 6 added**, in `tests/test_validate.py` beside the `grid` value tests —
`test_a_paired_path_must_be_a_real_parameter` (asserts the finding's `path` is
`sweep.paired[0].analysis.methdo`, so the loop's `where` is pinned, not just its code),
`test_a_paired_value_must_satisfy_its_param` (two parametrizations: outside-choices, wrong
type), the two unnameable tests, and
`test_a_legal_paired_axis_is_not_flagged_by_any_of_the_four` — the mirror, without which
deleting a check's *condition* rather than the check would pass every positive test.

**Mutation testing — three mutations, each discriminating a different helper.**
`find . -name __pycache__ -type d -exec rm -rf {} +` between every mutation and revert;
each revert verified by re-running the tests, never by `git status`.

| Mutation | Result |
|---|---|
| `_path_resolves(path, where)` → `path in spec` (report suppressed, no crash) | only `test_a_paired_path_must_be_a_real_parameter` fails; other 17 pass |
| `nameable=True` → `False` | exactly the two unnameable tests fail; `E-PARAM-VALUE` still reported |
| `_value_checks(...)` → `pass` | all four value tests fail; the path test still passes |
| revert | 18 paired tests pass; full suite 1079 |

An earlier variant of mutation 1 (removing the gate entirely) raised `KeyError` from
`spec[path]`, which is the could-fail proof that the gate is load-bearing rather than
decorative — and why the loop is gated on the path check first, as `grid`, `sample` and
`ablate.override` all are.

**Documents, same commit.** `reference.md`'s two registry rows named only `grid`,
`baseline` and `sample.ranges`; `sweep.ablate.override` was already missing from both, so
both were widened to the full enumeration rather than to `paired` alone. § How artifacts
are organized needed **no** edit: its sentence is already unscoped ("`validate` rejects a
swept value whose rendering isn't `[A-Za-z0-9._+-]+`"), which is exactly the internal
inconsistency the reviewer found — the two passages have disagreed since task 2 and the
code followed the narrower one. The code now matches the wider, and the rows now match the
code.

---

## Important — `W-SWEEP-BASELINE-CONFOUNDED`'s stated mechanism (`39477bf`)

**Documentation only**, as the brief permits. Widening `swept_axes` beyond `list(grid)` is
a behaviour change outside this fix's remit, and task 8's reviewer already declined a
softening of this row on evidence.

There are **two** falsehoods, not one, and both are now named in the row and at the emit
site:

1. The row explains its silence by per-cell expansion. That is the `grid` case only.
   `_baseline_cells` reads fixedness off the cells' paths and counts an axis fixed when the
   baseline names *any* of them, so a baseline half-fixing a multi-path `paired` axis
   makes it **fixed** — nothing expands, there is one baseline, and every
   comparison against it still differs on the paths the baseline left alone and is marked
   `confounded: true` at run time. In-tree corroboration: `contrasts.py`'s own docstring
   already states this ("a multi-path axis the baseline half-fixes counts as fixed in
   `_baseline_cells`"). The code is self-consistent; the row was what was wrong.
2. The guard reads `swept_axes = list(grid)`, so a `paired` axis is outside the check
   whether the baseline touches it or not — making the re-added remedy ("leave the ones you
   are stratifying over free") unreachable advice for such a user. The remedy sentence is
   kept and now says it holds for a `grid` axis.

The true half — a free *grid* axis expanding per cell — is kept verbatim rather than
deleted.

**Self-inflicted defect caught and fixed in `7fb6bb7`.** `39477bf`'s new emit-site comment
said "a multi-path `paired` (or `sample`) axis", which is the very defect class this
dispatch exists to close: a half-fixed `sample` axis beside a baseline is unreachable
(`E-SWEEP-SAMPLE-BASELINE` is unconditional on both being truthy), and it contradicted the
`check_swept_value` docstring `2023358` corrected on exactly that point. The comment now
names `paired` alone and cites the refusal that excludes `sample`. The `reference.md` row
was already correct — it names `paired` only.

**Test added**,
`test_a_half_fixed_paired_axis_is_silent_with_nothing_expanded_and_a_confounded_run`,
mirroring the existing `test_a_partly_fixed_baseline_is_silent_while_its_run_marks_confounded`
and asserting all three halves of the correction on the reviewer's exact probe: silent at
`validate`, exactly one baseline condition, and both comparisons differing on
`analysis.min_samples` *and* `analysis.confidence`. Could-fail proof: mutating
`_baseline_cells`'s `not any(...)` to `not all(...)` — the one-character change that would
make the row's stated mechanism true — fails the test; reverted, it passes.

---

## Three stale claims (`2023358`)

Comment/docstring only.

1. **`sweep.check_swept_value`** — "Every value in that cell is an axis value, checked here
   already as the axis's own" is now true, and stated with the reason it is true rather
   than left as an assertion: the only axes a baseline can leave free are `grid` and
   `paired`, both now checked. Verified rather than assumed — `E-SWEEP-SAMPLE-BASELINE`'s
   guard is the unconditional `if sweep.get("baseline") and sweep.get("sample")`, so
   `sample` can never be a free axis beside a baseline, and `ablate` is not an axis and
   composes with none (`E-SWEEP-ABLATE-CROSSED`).
2. **`contrasts._cell_paths`** — reframed rather than re-scoped. Pointing it at today's
   wider `E-SWEEP-VALUE-UNNAMEABLE` coverage would restate the same stale-by-construction
   claim: the function takes `expand`'s output and must not assume `validate` ran at all.
   The durable reason is that `!=` needs nothing of a value, which cannot go stale. The
   old justification's failure is kept as the parenthetical that explains the reframing.
3. **`cli._differing_axes`** — the retired `E-SWEEP-BASELINE-PARTIAL` claim is replaced by
   what the code does: since that retirement the two key sets can differ in **both**
   directions (a baseline may fix an axis the grid never sweeps, and a grid axis need no
   longer be fixed in the baseline), so the union walk with the `_MISSING` sentinel is
   *required*, not merely more defensive than the claim.

---

## Consistency passes

**Mechanical**, over `docs/*.md`, `README.md` and `CLAUDE.md`: relative links, `#anchor`
resolution, duplicate anchors, table row-vs-header column counts, trailing whitespace and
tabs — all clean, fenced blocks skipped. The three edited rows each carry their table's two
columns.

**Cross-document.** The class this touches is **Prevented mistakes**.
`experimental-designs.md` § Mistakes core prevents' "A typo'd parameter silently using a
default" row is unscoped — it rests on the schema being closed and `validate` checking
every key against it, naming no sweep mode — so it needed no edit and is *more* true after
this fix, not less. `reference.md` § Validation was read rather than assumed: its two
relevant rows ("Sweep paths resolve", "Swept values are nameable") name the check in the
first column and give a `sweep.grid` case in a column headed **Example failure**, so
neither is a scope claim and neither is stale. That table's own preamble says a row there
and a code in the registry "are the same check seen from the two ends", which is why only
the registry rows carried the enumeration and only they were widened. The worked example,
config completeness, enum comments, declared-vs-derived and versions are untouched by these
edits.

## Scope held

Not touched, per the brief: duplicate condition labels; the two document questions routed
to the `groups` slice; the three residual `ablate` value shapes; the two
`xfail(strict=True)` handles. No `E-SWEEP-AXIS-EMPTY` analogue for `paired: [{}]` and no
widening of `swept_axes` — both were considered and left alone as behaviour changes outside
the remit.

## Concerns

- **`E-SWEEP-PATH-UNKNOWN`'s row now also names `sweep.ablate.remove`/`override`** — the
  row was false for those before the edit and is true after, so this is closing the same
  omission rather than scope creep.
- **The half-fixed multi-path case is now documented as accepted-and-silent.** It is
  described in `docs/superpowers/spec-defects.md` as "Three baseline shapes per-cell
  expansion makes reachable"; whether such a config should be *refused* is still open and
  belongs with the slice that owns it. This fix only stops the document claiming a
  mechanism that does not run.
- **Mechanical pass** over `docs/*.md`, `README.md`, `CLAUDE.md`: links, anchors, duplicate
  anchors, trailing whitespace, tabs — all clean. The three edited rows each carry the
  table's two columns.
