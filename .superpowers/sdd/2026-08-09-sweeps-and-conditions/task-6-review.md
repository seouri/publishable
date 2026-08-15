# Task 6 review: `sweep.yaml`

## Verdicts

- **Spec compliance: ❌** — the document `sweep_document` builds does not match the
  `sweep.yaml` schema `docs/reference.md` § "`sweep.yaml` — the resolved plan" specifies,
  and the gap was not recorded in `docs/superpowers/spec-defects.md` as CLAUDE.md requires
  when implementation cannot follow the documents.
- **Task quality: findings** — code is otherwise clean, purity holds, and the round-trip
  tests are genuinely probing. The unrecorded spec conflict and a small report
  inaccuracy are the issues.

## Findings

### Important — `sweep_document`'s shape contradicts the documented `sweep.yaml` schema, unrecorded

`docs/reference.md` lines 491–507 give the literal `sweep.yaml` schema:

```yaml
design_digest: sha256:9c04...
conditions: [...]                        # matches the implementation
repeats:
  - kind: seed
    seeds: [17, 42, 137, 1009, 2027]      # one entry per KIND, seeds grouped
labels: [seed17, seed42, ...]             # composed labels, separate top-level key
order: as_declared                        # as_declared | randomized — the MODE, a scalar
execution_order:                          # the realized pairs, keyed condition/repeat
  - {condition: 0, repeat: seed17}
```

`sweep_document` (`src/publishable/sweep.py:154-175`) instead produces:

```python
"repeats": [{"kind": r.kind, "label": r.label, "seed": r.seed} for r in repeats],  # flat, one row per repeat, no `labels` key
"order":   [[index, label] for index, label in order],                            # a LIST of pairs
```

Two distinct problems:
1. `repeats` is shaped as one record per repeat rather than grouped by kind with a
   `seeds` list, and the top-level `labels` array (composed, outer-to-inner) is absent
   entirely — not deferred like fold membership, just structurally different.
2. `order` is reused for something reference.md defines as a different field with a
   different type: reference.md's `order` is the scalar mode (`as_declared`/`randomized`);
   the realized (condition, repeat-label) pairs belong under `execution_order`, as objects
   `{condition: ..., repeat: ...}`, not `[index, label]` lists. As written, whoever later
   wires this into the real `sweep.yaml` writer has no field left to record the mode
   without colliding with this one.

This traces back to `docs/superpowers/plans/2026-08-09-sweeps-and-conditions.md:809-819`
and the design doc (`specs/2026-08-09-sweeps-and-conditions-design.md:44`), which already
describe a simplified shape rather than reference.md's literal one — so the implementer
inherited it rather than introducing it. But the task-6-report.md claims "No spec defects
encountered; the brief's interfaces matched the actual `Condition`/`Repeat` shapes
exactly" (report, final paragraph) — true only about the Python types, not about the
document schema this artifact is supposed to produce. Task 2 in this same slice
(progress.md) escalated a comparable conflict (`__` separator vs. the swept-value
pattern) into `spec-defects.md` with candidate resolutions; this task's divergence from
reference.md's `sweep.yaml` example should have gone through the same process rather than
landing silently. Recommend logging it in `docs/superpowers/spec-defects.md` before the
task that wires this into the real writer (`cli.py` and/or a later S3a task) locks the
shape in further.

### Minor — report's test count doesn't match its own list

`task-6-report.md` says "Added four tests to `tests/test_sweep.py`" but lists three
bullets, and the diff confirms three new test functions (382 + 3 = 385, which the report's
own arithmetic states correctly two lines later). Cosmetic, but worth a one-word fix.

## What checks out

- **Purity.** `Repeat` is imported only under `if TYPE_CHECKING:` (`sweep.py:21-22`) and
  used solely as a forward-ref string annotation (`sweep.py:156`); no runtime import of
  `replication`, `config`, `artifacts`, `runner`, or `cli` was introduced. No filesystem
  access.
- **Resolved, not declared.** `sweep_document` reads `c.index`, `c.label`, `c.values`,
  `c.is_baseline` off the already-expanded `Condition` objects (`sweep.py:168-171`), never
  back from a raw config mapping — the resolved side is what lands in the document, per
  the invariant this artifact exists to protect. Seeds (`r.seed`) and the realized
  `order` are taken verbatim from their parameters rather than recomputed, matching "a
  field a consumer would re-derive is not a record."
- **Plain YAML-safe data.** `dict(c.values)` converts the `MappingProxyType` wrapper to a
  plain `dict` at the point it enters the document; `Repeat`'s fields are already plain
  `str`/`str`/`int`; `order` tuples become plain lists. `test_the_document_is_plain_yaml_safe_data`
  and `test_the_document_round_trips_a_float_and_a_boolean_condition_value`
  (`tests/test_sweep.py`, new) round-trip through `yaml.safe_dump`/`safe_load` and the
  latter asserts `isinstance(..., float)` / `isinstance(..., bool)` specifically — a real
  test of the MappingProxyType/type-coercion risk the brief called out, not one that only
  checks a single scalar key.
- **Condition ordering.** `sweep_document` iterates `conditions` in the order given
  without sorting or regrouping, and that order is `expand()`'s (baseline first, last
  declared axis fastest) — unchanged by this task and covered by pre-existing tests plus
  the new test's expected list.
- **Types/lint.** Signature matches the brief exactly; `list["Repeat"]` forward ref is
  valid under `from __future__` semantics already active in the file; nothing here should
  trip ruff's `UP`/`B` rules or mypy strict.

## Re-review

**Scope:** confirm the fix (`4221ed0`→`eaffd0a`, diff `review-e66a88b..eaffd0a.diff`) resolves the four divergences and introduces no regression.

- **Divergence 1 (repeats grouped by kind + top-level `labels`) — resolved.** `sweep_document` now groups `seeds_by_kind` and emits `"repeats": [{"kind": kind, "seeds": [...]}]` plus a separate `"labels": [r.label for r in repeats]` (`sweep.py:88-104`). Matches `reference.md:497-501` exactly, including key order.
- **Divergence 2 (`order` as scalar mode) — resolved.** `order` parameter's type changed from `list[tuple[int, str]]` to `str`; the doc field is now the literal mode (`"as_declared"`/`"randomized"`) with no re-derivation. Matches `reference.md:502`.
- **Divergence 3 (`execution_order` as a new key, `{condition, repeat}` objects) — resolved.** New `execution_order` parameter, rendered as `[{"condition": index, "repeat": label} for index, label in execution_order]` (`sweep.py:106-108`). Matches `reference.md:503-506` structurally (dict, not list-of-lists).
- **Divergence 4 (`order_seed` optional, only under randomized) — resolved and matches the second fenced example** (`reference.md:511-513`): written only `if order_seed is not None`, exercised by `test_a_randomized_order_records_its_seed`.
- **Tests assert the documented shape, not the old one.** `test_the_sweep_document_records_the_resolved_plan` checks grouped `repeats`, top-level `labels`, scalar `order`, dict-shaped `execution_order`, and `order_seed` absence. `test_the_document_round_trips_a_float_and_a_boolean_condition_value` now also asserts on the round-tripped `repeats[0]["seeds"]`, `labels`, and `execution_order` (not just top-level `conditions` values) — covers the new nesting as required. `isinstance` checks for `float`/`bool` are still present and unchanged.
- **Report's test count now correct.** Report claims "382 pre-existing + 4 net new" = 386, matching the observed 386 passed. The cumulative diff shows exactly 4 test functions relative to the `e66a88b` baseline (the original 3 were rewritten in place to the new shape; `test_a_randomized_order_records_its_seed` is the one genuinely new addition) — arithmetic and prose agree this time.
- **No regression found.** `Repeat` stays under `TYPE_CHECKING` only (`sweep.py:31-32`), no runtime import of `replication`/`config`/`artifacts`/`runner`/`cli` introduced, no filesystem access. Document remains plain built-ins throughout: `dict(c.values)`, plain `str`/`int`/`dict`/`list` — `order` went from a list-of-tuples to a plain `str`, if anything simpler than before; `execution_order` entries are plain dicts of `int`/`str`. Condition-ordering logic (`expand()` iteration, unchanged) untouched by this diff.

**Verdict: all four original findings resolved, no new Critical or Important finding.**
