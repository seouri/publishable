# Task 6 report — `stratify_by`, and strata that survive clustering

**Status: complete.** Commits `7f13c3e` (feature + tests + docs) and `8b98056` (a test-fixture
follow-up: `_animal_config` now writes the probe roster itself, so one argument decides both the
config and the table — a `varying=True` probe could otherwise be paired with a `varying=False`
roster) on `h3b-clustered-units-and-partitions`. This report is not in either commit:
`.superpowers/sdd/` is gitignored.
`uv run pytest` 1310 passed + 2 xfailed (was 1290 + 2); `ruff check` and `mypy` green.
`ruff format` not run.

## What landed

- **`units.stratum_varies_within_cluster(roster, cluster_by, stratify_by)`** — returns the first
  cluster (roster order) whose units disagree about the stratum, with the values it carries, or
  `None`. It **returns a fault rather than raising a code**, because the same computation serves
  three § Validation rows that name three different declarations (fold, holdout, `assign`), and the
  caller is what knows which. Cluster membership comes from `units.clusters_of` — task 2's single
  authority — so nothing here groups or counts clusters a second way, and a unit carrying no cluster
  value raises `E-DATA-CLUSTER-UNKNOWN` from there rather than being grouped alone and made
  trivially constant.
- **`validate._check_fold_stratify_by(doc, units_decl, roster, cluster_by, c)`** — both checks, two
  new codes:
  - `E-REPL-FOLD-STRATIFY-UNKNOWN` — the name is not in `data.units.attributes`, or is not an
    attribute name at all (non-string, `""`, `[]`).
  - `E-REPL-FOLD-STRATIFY-VARIES` — the declared stratum is not constant within some cluster under a
    declared `cluster_by`.
- **Wiring** — called from `validate_config` immediately after the `basis = fold_basis(...)` block
  and before `_check_replication`. It takes `usable_cluster`, **the existing local**, rather than
  re-reading and re-filtering `units_decl["cluster_by"]`: a second notion of "usable cluster
  declaration" is the near-miss class this slice keeps hitting.
- **Docs** — two rows in `reference.md` § Errors validate reports, in the `E-REPL-FOLD-*` block.
  Nothing else moved: the § Validation rows, line 132's `stratify_by` is NOT BUILT comment, and the
  § Validation NOT BUILT list all belong to task 11. `cohort-pilot` is untouched (it declares
  neither `cluster_by` nor a fold `stratify_by`).

## Where the survives-clustering check lives, and why

In `validate.py`, not `replication.py`. `_fold_k` sees a level dict, a count and a cluster *name*;
it has no roster, and the check needs cluster membership and the stratum's per-unit values together.
`validate_config` is the one place that holds the resolved roster beside the declaration, and it
already resolves `usable_cluster` there for `fold_basis`. The existence half sits in the same
function so the two can be ordered: when the attribute is not declared, `-UNKNOWN` is reported and
`-VARIES` is **skipped** — a derived second finding on top of the one the reader must fix anyway is
what `_check_cluster_by`'s own comment argues against.

Consequence for `REPL_DECLARATION_CODES`: **neither new code was added to it, deliberately.** That
frozenset translates a `replication.py` raise into a finding; both checks report through the
`Collector` directly, so a member there would be dead weight that reads like coverage. The brief
flags the frozenset as an obligation, so this is the answer to it rather than an omission.

## Scoping: the *"Stratification attribute exists"* row is only one-third discharged

The row names no particular `stratify_by`. This task implements **the `fold` level's only** — the
check reads `replication.repeats` and skips every non-`fold` level. `data.units.assign.<axis>.
stratify_by` (H3c) and `data.units.holdout.stratify_by` (H3d) are **not discharged**, and each will
want its own code (`E-DATA-ASSIGN-STRATIFY-*` / `E-DATA-HOLDOUT-STRATIFY-*` or whatever those slices
name). The codes here are fold-prefixed for exactly that reason: a shared `E-DATA-CLUSTER-STRATIFY`
would let a later slice believe its half was already built. Both new rows in § Errors validate
reports say "A `fold` level's" in their first clause, and the `-UNKNOWN` row states the split
explicitly. The *"Holdout strata survive clustering"* row is likewise untouched, though H3d can reuse
`units.stratum_varies_within_cluster` unchanged — that is what it was factored for.

## The ordering pins

`_fold_k` still raises `E-REPL-FOLD-STRATIFY-UNSUPPORTED` before `k` is read; **nothing about that
raise was touched** (task 11 retires it). Two pins assert what today's configs report *and that the
flip code is absent*, which is what makes task 11's change show up as a diff:

| Config | Reports today | Asserted absent today, expected once the raise retires |
|---|---|---|
| `{kind: fold, k: 1, stratify_by: label}` | `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | `E-REPL-FOLD-K` |
| `{kind: fold, k: 99, stratify_by: label}` over a 15-unit roster | `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | `E-REPL-FOLD-K-TOO-LARGE` |

The `k: 99` pin resolves a real roster (15 units) so the ceiling it is pinning the *absence* of is
genuinely reachable — with no roster the flip would be unreachable and the assertion vacuous.

## Tests (20 new: 5 in `test_units.py`, 15 in `test_validate.py`)

**Fixture, shared by both files:** 15 cells over 5 animals sized **7/3/3/1/1**, `label` per animal;
the probe flips **one** cell of the three-cell animal `A3`. It discriminates because neither
coincidence holds: three animals hold several cells each, so a stratum is not constant within a
cluster merely for the cluster being a singleton; and `label` takes both values across the roster, so
it is not globally constant either. Probe and control differ by that one cell, so the control is
discriminating rather than decorative. It also matches the § Validation row's own example, which
names animal `A3`.

| Where | Probe | Control that must report |
|---|---|---|
| `test_units.py` | varying `label` → `("A3", ["normal", "tumor"])` | same 15 cells, `label` constant within each animal → `None` |
| `test_units.py` | a cell with no stratum value varies from its siblings | two cells both carrying none → `None` |
| `test_units.py` | a unit with no *cluster* value → `E-DATA-CLUSTER-UNKNOWN` from `clusters_of` | — |
| `test_validate.py` | through `validate_config`: `stratify_by: label` undeclared → `-UNKNOWN` **beside** `-UNSUPPORTED` | `label` declared → no `-UNKNOWN`, `-UNSUPPORTED` still there |
| `test_validate.py` | direct `_check_fold_stratify_by(..., roster=None, cluster_by=None)` → exactly `-UNKNOWN` | same call with `attributes: [label]` → no findings |
| `test_validate.py` | parametrized `""`, `[]`, `["label"]`, `3` → `-UNKNOWN` | a level with no `stratify_by` at all (plus a `seed` level) → no findings |
| `test_validate.py` | through `validate_config`: varying `label` + `cluster_by: animal_id` → `-VARIES` **beside** `-UNSUPPORTED` **and** `E-DATA-CLUSTER-UNSUPPORTED` | constant `label`, same design → no `-VARIES` |
| `test_validate.py` | direct call with a 2-cell `A3` → exactly `-VARIES`, message names `A3` | same call, both cells `tumor` → no findings |
| `test_validate.py` | the same varying roster with **no** `cluster_by` → no finding (nothing indivisible) | — |
| `test_validate.py` | undeclared *and* varying → exactly `-UNKNOWN`, one finding not two | — |
| `test_validate.py` | a unit with no cluster value → silence, `validate` never raises | — |
| `test_validate.py` | the two ordering pins above | — |

Both live refusals (`E-REPL-FOLD-STRATIFY-UNSUPPORTED`, `E-DATA-CLUSTER-UNSUPPORTED`) still fire, so
every `validate_config` probe **asserts the refusal appears alongside** the new finding — the proof
the check was reached rather than shadowed — and every check is **also** exercised by a direct call,
which no refusal reaches.

**Totality over `stratify_by`:** non-string, empty string, empty list, a name some units lack, a
name no unit declares, and declared with no `cluster_by`. One judgement worth flagging: there is
**no `E-CONFIG-TYPE` backstop** inside a repeat level — `envelope.LEAF_TYPES` types
`replication.repeats` a `list` and nothing under it — so unlike `data.units.cluster_by` a non-string
could not be "left to the envelope". A list form (`[label]`, which `holdout`/`assign`/`resample` all
take and a reader will plausibly write on a fold) is therefore reported here, under `-UNKNOWN`, and
the § Errors row says so.

## Mutations (each reverted; reverts verified by the full suite, never `git status`)

`__pycache__` deleted between each mutation and its revert.

| Mutation | Failing tests | The other check's tests |
|---|---|---|
| `if declared not in {*names, declared}:` — the existence check's reference set made unfailable | `test_a_fold_stratify_by_naming_no_attribute_is_reported`, `test_the_fold_stratum_name_check_reports_without_a_roster`, `test_an_undeclared_fold_stratum_is_not_also_reported_as_varying` (3 failed) | all `-VARIES` tests **passed** |
| `if len(seen[cluster]) > 99:` in `units.stratum_varies_within_cluster` — the clustering check made unfireable | `test_a_stratum_varying_inside_a_cluster_is_found`, `test_a_cell_carrying_no_stratum_value_varies_from_its_siblings`, `test_a_fold_stratum_varying_within_a_cluster_is_reported`, `test_the_fold_stratum_clustering_check_runs_on_a_direct_call` (4 failed) | all `-UNKNOWN` tests **passed** |

Disjoint failure sets in both directions: two checks, two tests, not one mutation killing both.

## Concerns / gaps for later slices

1. **`-UNKNOWN` fires with no `data.units` at all.** `{kind: fold, stratify_by: x}` and no `data.units`
   reports `E-REPL-FOLD-NO-UNITS` *and* `-UNKNOWN` ("`attributes` declares none"). That is
   `_check_weight_by`'s stated precedent — "no attributes are declared, so it names none of them" —
   and the pre-existing `test_fold_stratify_by_is_refused_through_validate` (which has no
   `data.units`) still passes, but a reader gets two findings for one missing block.
2. **Nothing consumes a validated `stratify_by` yet.** `partition_units` takes no strata, so these
   are declaration checks standing ahead of an unbuilt partitioner — by design (task 11 retires the
   refusal), but § Repeat kinds' "`fold` | data partition — k-fold, **stratified**, or …" row stays
   describing code that does not exist until stratified partitioning lands. Task 5's concern 4 names
   the cluster-membership half of the same row; this is the stratified half.
3. **`assign` and `holdout` halves are open**, as § Scoping above states. Whichever slice builds them
   should call `units.stratum_varies_within_cluster` rather than re-deriving membership, and should
   *not* reuse `E-REPL-FOLD-STRATIFY-*` — a `data.units.holdout` fault reported under a `E-REPL-FOLD-`
   code would misname the block the reader has to edit.
4. **A cell carrying no stratum value is reported as a variation** (rendered `no value` among the
   values). That is a judgement, not a documented rule: the alternative is a dedicated
   "stratum missing for some units" finding, which no § Validation row currently asks for. Tested
   both ways (mixed → refused, all-missing → silent) so the behaviour is pinned rather than
   incidental.
5. **No documented example is newly refused** — checked, since a check that refuses a config the
   documents show is the cross-document class no grep sees. The four documents show a fold
   `stratify_by` twice, both in fragments that declare no `data.units` at all (`reference.md`
   § Statistical reporting's nested `fold × seed` block, `experimental-designs.md`
   § Cross-validation), and the full schema in `reference.md` § The one config file declares
   `attributes: [label, age, sex]` with a `seed` level. The feasibility analysis's `stratify_by: [truth]`
   entries are `holdout` and `resample` blocks, not fold levels, and `truth` is declared. Nothing to fix.
6. **The brief was accurate.** No defect found in it; the only thing it left open — where the
   clustering check lives — is answered above.
