# Task 1 review: `Comparison` and contrast resolution

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## Purity

`src/publishable/contrasts.py` imports only `dataclasses.dataclass` and
`typing.{TYPE_CHECKING, Any}` at runtime; `publishable.sweep.Condition` is
imported solely under `TYPE_CHECKING` (contrasts.py:8-9 in the new file,
diff lines 28-29). No filesystem access, no runtime import of `config`,
`artifacts`, `runner`, or `cli`. Nothing else crept in — the whole file is
the dataclass and one function.

## The empty case

`test_no_baseline_and_no_declared_contrasts_yields_nothing` (test_contrasts.py
diff lines 84-86) asserts `resolve_contrasts({}, conds) == []` against two
non-baseline, labelled conditions. That's a real pin, not an incidental pass:
if the baseline-lookup branch had used something falsy-but-not-`None` as a
sentinel, or if the loop fired without a baseline present, this would catch
it. Good — matches the brief's "no `vs_baseline` block at all" intent, which
is enforced one layer up (this module just needs to return `[]`, which it
does).

## `label=None`

`resolve_contrasts` excludes label-`None` conditions from `by_label` and
skips them in the baseline loop (`c.label is not None` guard, contrasts.py
line matching diff 54). This is the right behavior — a `None` label can't be
named by a config and must not become a comparison id. In practice, given
`sweep.expand`'s current invariants (checked in `src/publishable/sweep.py`),
label is `None` only for the single implicit condition of a no-sweep run, and
that condition is never `is_baseline=True` (it's constructed with
`is_baseline=False`, sweep.py `expand`). So today the guard is unreachable
dead code — the no-sweep case already returns `[]` via the "no baseline"
branch, never via this guard — but it's cheap, correct insurance against a
future change to `expand`'s invariant, and not a defect.

No test exercises this guard directly (no test mixes a `label=None` condition
with an actual baseline). Given it's currently unreachable per `sweep.py`,
that's a minor gap, not a real one.

## Ordering

`test_declared_contrasts_come_after_the_baseline_ones` (diff lines 128-136)
pins `[method=spearman, extra]`, i.e. `vs_baseline` entries before declared
ones, matching the brief's "record's order." The implementation appends the
baseline loop's output before the declared-entries loop, so order falls out
structurally rather than being sorted after the fact — nothing to game here.

## The `KeyError`

The comment is present (diff lines 57-60) and accurate: it names Task 6 as
the validate-time guard and states `cli` always validates first, matching
the brief's own justification word for word. `by_label[entry["of"]]` /
`by_label[entry["against"]]` will indeed raise `KeyError` on an unresolvable
label — verified by reading the dict-literal construction; no defensive
`.get()` masks it.

## Tests as evidence

| Test | Catches |
|---|---|
| `test_no_baseline_and_no_declared_contrasts_yields_nothing` | A stray comparison being emitted with no baseline and no declared entries (e.g. treating an empty `contrasts: []` list as `None` incorrectly, or iterating conditions without checking baseline presence) |
| `test_each_non_baseline_condition_compares_against_the_baseline` | Wrong `of`/`against` indices, wrong `id` (label vs. something else), extra baseline-self comparison (the tuple list would have 3 entries with `(0,0)` present if the `c.index != baseline.index` filter were dropped — this **does** catch the baseline-against-itself case), and wrong order between the two non-baseline conditions |
| `test_a_declared_contrast_resolves_labels_to_indices` | Label→index resolution being backwards (`of`/`against` swapped) or `within` defaulting to something other than `None` when absent |
| `test_a_declared_contrast_carries_its_within_stratum` | `within` being dropped or overwritten instead of passed through |
| `test_declared_contrasts_come_after_the_baseline_ones` | Declared entries being interleaved with or placed before `vs_baseline` entries |

Confirmed: the baseline-vs-itself case is caught, via the tuple-list equality
check in the second test — an implementation that failed to exclude the
baseline from its own loop would produce a 3-element list where the test
expects 2, failing on both length and content.

## Minor findings (non-blocking)

- `entry.get("id")` silently coerces a missing `id` to the string `"None"`
  rather than raising. Acceptable under the same "Task 6 guards this at
  validate time" reasoning applied to `of`/`against`, but the code comment
  only mentions the `KeyError` path, not this one. Worth a follow-up comment
  if Task 6's validation doesn't also require `id`.
- `within=entry.get("within")` passes through the caller's dict by reference
  rather than copying it into the frozen `Comparison`. Since `Comparison` is
  otherwise immutable this is a small crack in that guarantee, but harmless
  in practice since nothing downstream is shown to mutate it.

## Export question

`Comparison` and `resolve_contrasts` are not added to
`src/publishable/__init__.py`'s `__all__`. Conclusion: correct as is — a user
never imports `Comparison` directly; contrasts are declared in YAML
(`statistics.contrasts`) and consumed internally between `sweep`, this
module, and whatever downstream statistics/report code Task 6+ wires up.
`Comparison` is an internal record type analogous to `sweep.Condition`
itself (which also isn't exported), not part of the user-facing surface
`reference.md` § The importable surface enumerates. No action needed here.
