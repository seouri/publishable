# Tasks 7 and 8 report — the `assign` cross-field checks

**Status:** Complete.
**Commit:** `e288653` (amended once, for the registry row order below) — `feat(validate): a `between` design names its arms, and each assignment names a method`. One commit, not two: the two tasks are one function reading `data.units.assign` once, and splitting the diff would have produced an intermediate state nobody reviews.
**Tests:** `uv run pytest` → **1427 passed, 2 xfailed** (was 1408 + 2). 19 new tests. `ruff check` and `mypy` green; `ruff format` not run.

## What landed

`validate._check_assign(doc, units, c)`, called from `validate_config` immediately after
`_check_cluster_by`, plus `ASSIGN_METHODS = ("random", "by_attribute", "blocked")` as the
single source of the enum. Three § Validation rows, **none of which had an implementation**:

| Row | Code | Fires when |
|---|---|---|
| *Allocation needs arms* | `E-DATA-ALLOCATION-NO-ARMS` | `allocation: between` and `sweep.groups` yields no readable axis name |
| *Every axis is assigned* | `E-DATA-ASSIGN-MISSING` | `between` and a declared axis has no block — **one finding per axis**, declaration order |
| *Assignment names a method* | `E-DATA-ASSIGN-METHOD` | `method` absent/`null`, out of enum, or the block is not a mapping |

**Task 1's finding was followed rather than paraphrased.** The REQUIRED-when-`between` rule
gets no code of its own: the first two rows cover absent `assign`, `assign: {}`, `{arm: null}`,
and `between` with no axes, between them. Each of those four shapes has a test.

**Gating, and why.** The first two rows are gated on `allocation == "between"`; the method check
is not, because it is a check on the block rather than on a pair of declarations. Under
`allocation: within` a declared group axis is *Arms need allocation*, a different fault — see the
concern below.

Three rows added to § Errors `validate` reports, inserted in the table's alphabetical position
(before the first `E-DATA-CLUSTER-*` row). Mechanical pass clean, and proved able to fail: an
extra cell and trailing whitespace planted on the new rows were both flagged. The remaining
findings my throwaway checker printed are its own slugger's false positives on `--` anchors
(`#secrets--credentials` and friends), pre-existing and untouched.

## Proving the checks are not dead

Every config-level assertion is an **exact error set** taken beside the live refusals
(`E-DATA-ALLOCATION-UNSUPPORTED`, `E-DATA-ASSIGN-UNSUPPORTED`, `E-SWEEP-GROUPS-UNSUPPORTED`),
and every check is **also reached directly** through `_check_assign` with a bare `Collector`.
The control — a valid `assign` block — asserts its own exact set of three refusals rather than
an absence, so it must report.

One shape needed spelling out per-case rather than smoothing: `{arm: null}` carries
`E-DATA-ASSIGN-UNSUPPORTED` and `{}` does not, because that refusal tests truthiness. Stated in
the test instead of being hidden behind a looser assertion.

**Four mutations, four separate kills**, `__pycache__` deleted each time and every revert
verified by re-running the suite:

| Mutation | Killed |
|---|---|
| `if not axes:` → never | `test_between_allocation_with_no_group_axis_has_no_arms` only |
| `if blocks.get(axis) is None:` → never | the three `..._no_assign_block_is_refused` cases and `..._each_unassigned_axis...` only |
| `if method is None:` → never | `test_an_assignment_declaring_no_method_is_refused` only |
| `elif method not in ASSIGN_METHODS:` → never | the enum test and two malformed-shape cases |

**The third mutation initially killed nothing, and that is worth keeping.** The presence and
enum branches share one identifier, so with the presence branch deleted `None` falls through to
the enum branch and reports the same code saying the wrong thing. The test now asserts the
message (`"not declared"`), which is what makes the branch separately testable.

## Registry integrity, checked in both directions now rather than at task 20

Each of the three codes appears in exactly one § Errors `validate` reports row and in
`validate.py` (`--include='*.py'`, with `__pycache__` already deleted by the mutation runs); a
control code that exists nowhere returns nothing, so the grep discriminates. The commit contains
exactly `docs/reference.md`, `src/publishable/validate.py`, `tests/test_validate.py`.

**The table is sorted by code, and my first placement was not** — `METHOD` sorts before
`MISSING`. Fixed by amending the commit. Sorting the code column is a check the mechanical pass
does not perform, and running it turned up one **pre-existing** violation:
`E-SWEEP-ABLATE-BASELINE-GROUP` sits after `E-SWEEP-ABLATE-CROSSED` (task 5's row). Left alone —
it is not this task's row — and flagged here for task 20 step 3.

## Concerns

1. **`groups` + `allocation: within` is reported by nothing, and no task owns it.** That is
   § Validation's *Arms need allocation* row — outside these two tasks, since it reads
   `allocation` and `groups` rather than the `assign` block. Once task 17 retires
   `E-SWEEP-GROUPS-UNSUPPORTED` and `E-DATA-ALLOCATION-UNSUPPORTED`, `groups: [arm]` under the
   default `within` with no `assign` **validates clean and runs**, handing every condition the
   whole roster — verbatim the "two identical measurements reported as two arms" that task 20
   step 6 requires to be structurally impossible and asks which task provides. Today the answer
   is none. Deliberately not added here.
2. **`E-DATA-ALLOCATION-UNSUPPORTED`'s message is now stale.** It says group axes "are not
   implemented either"; task 5 made them expand. Task 17 owns that message — routed there
   rather than edited under a task that retires nothing.
3. **A malformed `groups` entry (`[{by: 123}]`) makes `between` report *Allocation needs arms*.**
   `selector_paths` yields no name, so the design genuinely has no readable axis. Acceptable
   while `groups` has no `_check_shape` guard (task 5 routed that to task 17); stated in the
   docstring and the registry row rather than left to be discovered.
4. **Ungating the method check has a visible consequence, named so it is not read as complete.**
   `assign: {cohort: {}}` under the default `within` with no `groups` axis now reports
   `E-DATA-ASSIGN-METHOD`, while the deeper fault — *Every assignment names an axis*, also
   unimplemented — stays silent. The ungating is still right; the finding is just not the whole
   story for that config.
5. **Neither brief was defective.** Both are accurate; task 1's "these two rows already cover it"
   was correct and is what this implements.
