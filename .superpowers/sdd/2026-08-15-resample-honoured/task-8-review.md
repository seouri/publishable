# Task 8 review: `limits.min_clusters` made real

**Spec compliance: ✅** — the design doc's task 8 asks for § Validation's *Clusters enough to resample*
made real plus the one-line `stats.py` docstring fix; both shipped. `reference.md`'s new
§ Warnings core reports row is alphabetically placed (REPORTBY-THIN < RESAMPLE-CLUSTERS <
RESAMPLE-FAMILY), 3-pipe like every sibling, no trailing whitespace anywhere in the file, and no
count phrase near it to invalidate. `limits.min_clusters` is read from the doc with no injected
default, which is the pattern `max_executions` and `min_reported_n` already follow.

**Task quality: APPROVED WITH FINDINGS** — 3 Important, 5 Minor. No behavioural defect shipped.

## Verified by behaviour (not by reading)

Tree restored and confirmed at the committed state: `uv run pytest` → **1726 passed, 2 xfailed**,
`ruff check` and `mypy` clean; `validate.py` md5-identical to the pre-mutation copy after every
mutation.

- **The fixtures are not vacuous.** Probe: `_FOUR_ANIMALS` resolves a roster of **12 units in 4
  clusters**, and `validate` reports `W-STATS-RESAMPLE-CLUSTERS` with "4" in the message. This is
  *not* the trap the original `_RESAMPLE_UNITS` fell into — the CSV carries the declared attribute
  and `roster` is a real `UnitList`.
- **Not a proxy count.** `fold_basis` → `cluster_count` → `clusters_of`, and `cli.py:1175` builds the
  membership handed to `percentile_over_units_clustered` from that same `clusters_of`. The number
  warned about is the number the interval would actually draw.
- **The decisive cluster-count property holds** (though no test asserts it — see Minor 5): the same
  config over a 12-unit/**12-cluster** roster at floor 10 is silent, and over 12 units/4 clusters
  warns. Only the cluster count moved.
- **Brief mutations reproduce.** `fold_basis(roster, cluster_by)` → `len(roster)` fails
  `test_a_clustered_resample_below_min_clusters_warns` and `..._counts_clusters_not_units`;
  `groups < min_clusters` → `groups < 10` fails `..._is_silent_above_the_floor`.
- **`E-DATA-CLUSTER-UNKNOWN` is not double-reported and `validate` still collects.** Reachable case
  is `cluster_by` naming `measurements.by`: the `except ContractError` branch *is* taken (proved by
  making it raise), and the whole finding set is `E-STATS-RESAMPLE-UNSUPPORTED` alone.
- **`min_clusters` is guarded.** `"ten"`, `True` and `10.0` each yield `E-CONFIG-TYPE` only; no
  crash, no warning.
- **Brief-defect substitution is syntax only.** `write_config` assigns the final leaf of a dotted
  path and never creates intermediates, and `base_config` has no top-level `limits` — so the brief's
  literal `"limits.min_clusters": 10` raises `KeyError: 'limits'` in the fixture. Confirmed. The
  floors shipped are 10/10/3/10 exactly as briefed, and since `base_config` carries no `limits` at
  all, the nested form produces the identical document the dotted form would have. Nothing but
  syntax changed.

## Important

**IMPORTANT 1 — the comment at `validate.py:5033-5037` is now false, and it is the same comment
that already cost this slice two swallowed findings.** It reads: "`roster` is unused by every check
below (`method`, `n`, the family bound, and `stratify_by` all read `resample`/`doc` alone), so a
missing roster does not make any of them unsafe to run." Task 8 adds a check below it that reads
`roster`, and the enumeration does not list it. No consequence today — the new check is
`roster is not None`-guarded — but task 7's review established that *this exact comment* is what
justified a `return` suppressing `E-STATS-RESAMPLE-METHOD` and `-N`. A later task trusting it could
restore that `return` and silently kill this check. Amend the enumeration in place.

**IMPORTANT 2 — the new `except ContractError` comment claims a guarantee the code does not
provide.** It says the fault is "already reported beside this by `_check_cluster_by` or by the
resolution `_check_units` performed." Measured: with `cluster_by: read_id` and
`measurements.by: read_id`, the branch fires and **nothing reports `E-DATA-CLUSTER-UNKNOWN`** —
`_check_cluster_by` tests the declaration against `attributes`, not each unit's value, and
`validate_config:603-612` says so explicitly ("has no validate-time reporter … a config in that
shape validates clean and raises at `run`"). This is the fifth false-guarantee comment in
`_check_resample`. The wording was copied verbatim from the sibling at `validate.py:2623`, which
carries the same falsehood — naming that propagation path is what stops task 9 copying it a third
time. `validate.py:2043`'s narrower claim (`_check_cluster_by` only) is the same shape.

**IMPORTANT 3 — three of the four guard clauses are untested; the suite is green under each
mutation.** Ranked by consequence:

- `roster is not None`: deleting it leaves **1726 passed**. It is load-bearing — a config with
  `data.units.from: missing.csv` plus `cluster_by` plus `resample` then dies with
  `TypeError: 'NoneType' object is not iterable` out of `units.py:868`, i.e. `validate` raises where
  it is contracted to collect.
- `isinstance(cluster_by, str) and cluster_by`: deleting it leaves **1726 passed**, while a config
  with `resample` + `min_clusters: 10` and **no** `cluster_by` then reports the nonsense
  "`data.units.cluster_by: None` puts this roster in 1 clusters". The brief's fourth test covers the
  *resample* half of the gate (and does so via the function's own early `return`); the `cluster_by`
  half — the half the review brief asked to check — is covered by nothing.
- `isinstance(min_clusters, int) and not isinstance(..., bool)`: correct, untested.

**IMPORTANT 3b — the report asserts coverage that does not exist.** § Concerns says "both the
roster-is-`None` and the `E-DATA-CLUSTER-UNKNOWN` paths are guarded and tested for silence."
Guarded, yes; **tested, neither**. Recorded separately from the coverage gap because the next task
reads this report, and an unchallenged "tested" claim is how an untested guard gets built on.

## Minor

1. **The miscitation survives in a tracked file.** `tests/test_stats.py:2206` still says the judgment
   "belongs to `statistics.min_clusters`, which `validate` warns on" — a path that does not exist in
   `envelope.LEAF_TYPES`. The report's claim ("no other miscitation in `src/` or the four
   documents") is true as scoped and simply never covered `tests/`. Sweep run by filtering the file
   list (`git ls-files | xargs grep`), not the output: the only other hits are `docs/superpowers/`
   planning records, which are the historical record and correctly left alone.
2. **`_check_resample`'s docstring first line still enumerates only** "`method` enum, its `n` floor,
   the comparison-family lower bound … and its `stratify_by` names" — an enumeration reading as
   complete that now omits a fifth check.
3. **Two call sites of the one derivation the comment calls single.** `validate_config:598-613`
   already computed this exact number as `basis`, from an independently re-derived `usable_cluster`
   whose logic the new block duplicates (`isinstance(str) and truthy`). Identical today, so no bug —
   but the number is walked twice and a future change to `usable_cluster` diverges silently. Passing
   `basis` in would make the comment's claim true.
4. **Test redundancy inherited from the brief.** `test_the_cluster_warning_counts_clusters_not_units`'s
   first assertion duplicates `test_a_clustered_resample_below_min_clusters_warns` outright, and its
   second `write_config` call re-writes a byte-identical config only to read messages instead of
   codes.
5. **No test varies the cluster count with the floor fixed.** The positive companion varies the
   *floor* (10 → 3) on one roster. Verified by probe that the behaviour is right (12 clusters at
   floor 10 → silent), so this is coverage, not correctness — but a 12-cluster fixture asserting
   silence at floor 10 is the one test that pins "the cluster count is what moved".

## Not findings

- The early `return` at `validate.py:5017` is the real gate on "resample declared"; the fourth test
  passes through it. Correct, if indirect.
- No default is injected for an absent `limits.min_clusters`. Matches `max_executions` /
  `min_reported_n`.
- `E-STATS-RESAMPLE-UNSUPPORTED` accompanies every one of these configs, as it will until task 12;
  it proves nothing here and was not leaned on.
