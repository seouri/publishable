# Task 11 report: the expansion modes the union must cover

**Status:** complete. No change to `src/publishable/validate.py` was needed — all four fixtures
passed against task 10's shipped implementation once the fixtures themselves were shaped correctly
(see disagreements below).

**Commit:** `e74f39a4deb40f27c1770fa9f8f767b0f93e9a90` —
`test: the union over baseline, paired, groups, and ablate.remove` — since amended in place (see
"Review round" below); the final tree is what's described throughout this report.

**Test summary:** `uv run pytest` — 1989 passed, 2 xfailed (baseline 1985 + 2 xfailed, plus the 4
new tests in this task). `uv run ruff check .` clean. `uv run ruff format --check .` clean (76
files, 0 to reformat — the brief's literal test code needed one `ruff format` pass, same as task
10). `uv run mypy` clean (43 source files).

## Step 2: what each fixture did against the shipped code

All four passed immediately, once shaped to match `sweep.py`'s actual schemas (see below) — task
10's implementation already generalizes to all four expansion modes. No `validate.py` change.

## Step 3: unrelated findings, checked and attributed

Printed `codes(path)` for each fixture (temporarily, removed before commit):

| Fixture | `codes(path)` | Attribution |
|---|---|---|
| baseline | `{E-CRED-PARAM-MISSING}` | clean |
| paired | `{E-CRED-PARAM-MISSING}` | clean |
| groups | `{E-CRED-PARAM-MISSING, E-DATA-ALLOCATION-WITHIN-ARMS}` | the second is `sweep.groups` declaring an axis under the default `allocation: within` — [§ Validation](../../../docs/reference.md) *Arms need allocation*, unrelated to credentials and expected for any `groups`-only config that doesn't also declare `allocation: between`. Not weakened away — the test's assertion is membership (`f.code == "E-CRED-PARAM-MISSING"`), not set equality, so this finding does not need suppressing |
| ablate.remove | `{E-CRED-PARAM-MISSING}` | clean |

## Step 4: the prescribed mutation

`for condition in conditions:` → `for condition in conditions[:1]:` in `_check_requires_env`.

- `test_a_baseline_is_a_resolved_condition_whose_credential_joins_the_union` — **PASSED** (blind).
  Confirmed the brief's reasoning: `expand` emits the baseline row first (`c.index == 0`), so
  truncating to the first condition still sees it.
- `test_a_paired_cell_resolves_both_of_its_paths` — **FAILED**, as the brief names, because
  `expand` orders the `azure_openai` cell (condition 0, key already set) before the `ollama` cell
  (condition 1, the one requiring `OLLAMA_TEST_KEY`), and truncation to `conditions[:1]` drops the
  second entirely. Verified `[c.values for c in expand(doc)]` before trusting the ordering claim.
  The exact manifestation changed during the review round below — after switching this test's
  assertion from `messages_by_code` to a counted `_findings_of` list, the mutation now surfaces as
  `AssertionError: assert 0 == 1` (`found == []`) rather than the `KeyError` the brief predicted
  against the pre-review assertion shape; re-verified directly rather than left as a stale claim.
- `test_a_groups_axis_contributes_no_parameter_value` — **PASSED** (blind). Both group cells resolve
  the identical `llm.provider` default, so condition 0 alone already carries the finding.
- `test_ablate_remove_resolves_a_value_with_no_key_and_requires_nothing` — **PASSED** (blind). The
  baseline condition (the only one that reports) is condition 0.

Reverted by editing back (`for condition in conditions:`); `__pycache__` cleared; re-ran — all four
green; `diff` against a pre-mutation copy of `validate.py` confirmed byte-identical (not `git
status`).

Also ran the brief's named "obvious" mutation for completeness — deleting the
`if path in condition.selectors: continue` guard — against all four new fixtures. **Blind on all
four**, as the brief predicts: none of the four axis names a `groups` cell that collides with a
`parameter_spec` path the way task 10's own
`test_a_group_axis_colliding_with_a_credentialed_parameter_still_runs_the_check` does, so `wanted`
never contains the group axis's key regardless of the skip. Reverted; re-ran; confirmed green.

## Step 4's second mutation: `first_seen.setdefault` → `first_seen[…] = …`

Ran it. `test_a_variable_two_conditions_need_is_reported_once` (task 10's) **failed** as predicted —
it does pin attribution already, via `assert "condition \`provider=openai__retries=1\`" in
found[0].message`; under the mutation this becomes `provider=openai__retries=2` and the assertion
fails. So this mutation is **already pinned** by an existing test; nothing needed adding there.

But the brief's suggestion to add a pinning assertion "in the paired fixture" does not hold up: the
paired fixture (`test_a_paired_cell_resolves_both_of_its_paths`) has exactly one condition needing
`OLLAMA_TEST_KEY` and one needing nothing (its key is set) — there is no attribution race in it at
all, so a first-vs-last-wins mutation cannot be distinguished there. The fixture that *does* carry a
second, independent attribution race among this task's four is **groups**: both group cells
(`cohort=derivation`, `cohort=validation`) resolve the identical `llm.provider` default and so need
the identical variable, with two different condition labels available to attribute it to. I added
one assertion to `test_a_groups_axis_contributes_no_parameter_value`:

```python
assert "condition `cohort=derivation`" in found[0].message
```

Verified: passes against the shipped code (`expand` emits `cohort=derivation` before
`cohort=validation`), and fails under the `first_seen[…] = …` mutation with the message correctly
showing `condition \`cohort=validation\`` instead. Reverted the mutation; diffed clean; re-ran full
`test_validate.py` (696 passed).

## Step 5: the ablate.remove silence — covered by count, not by mutation

As the brief anticipates, no single-line mutation makes
`test_ablate_remove_resolves_a_value_with_no_key_and_requires_nothing`'s silence go red. The
behaviour under test is "does nothing" — `param.requires_env.get(value)` returns `None` for the
ablated `null` value, contributing no entry to `first_seen` — and every plausible one-line mutant
that would make it report something (e.g. defaulting the `.get` to a non-`None` fallback) is not a
change any of this task's fixtures would produce from a realistic implementation slip; the
mutations that *are* realistic (the two run above) don't touch this line at all. The property is
proved instead by the count assertion (`len(found) == 1`) together with the baseline control on the
same document — if `.get(value)` on the absent `None` key ever stopped returning `None`, that count
assertion is what would catch it, going to 2. Stated as covered-by-count per the brief's own framing,
not defended as mutation-proof.

## Per-test discriminating mutation, named directly

| Test | Discriminating single-line mutation |
|---|---|
| `test_a_baseline_is_a_resolved_condition_whose_credential_joins_the_union` | Not the prescribed `conditions[:1]` (blind — baseline is condition 0). Found empirically: inserting `if condition.is_baseline: continue` at the top of the per-condition loop body — makes the baseline's own resolved value invisible to the union. Verified: fails with `found == []`. Reverted, diffed clean. |
| `test_a_paired_cell_resolves_both_of_its_paths` | The prescribed `conditions[:1]` — the one test in this task the brief names as the mutation's target, and the only one of the four it actually catches. |
| `test_a_groups_axis_contributes_no_parameter_value` | `first_seen.setdefault(...)` → `first_seen[...] = ...`, **discriminable only after** adding the `condition \`cohort=derivation\`` attribution assertion (see above) — without that assertion this mutation is blind here too, since the count and membership assertions alone don't see which cell won. |
| `test_ablate_remove_resolves_a_value_with_no_key_and_requires_nothing` | Same `if condition.is_baseline: continue` mutation as the baseline test — the ablate test's sole finding comes from its baseline condition, so removing baseline-condition resolution empties `found` here too (`found == []`). |

## Where the brief or the spec disagreed with the code

1. **`sweep.groups`'s brief-given shape is wrong.** The brief's fixture used
   `"sweep": {"groups": {"cohort": ["derivation", "validation"]}}` — a dict keyed by axis name.
   `sweep.py`/`docs/reference.md` § The one config file define `sweep.groups` as a **list** of
   `{by, levels}` blocks (matching the shape already used elsewhere in this same file, e.g.
   `test_a_group_axis_colliding_with_a_credentialed_parameter_still_runs_the_check`). Run verbatim,
   the brief's dict shape earns `E-CONFIG-SHAPE`/`E-CONFIG-TYPE` before reaching any credential
   check. Corrected to `"sweep": {"groups": [{"by": "cohort", "levels": ["derivation", "validation"]}]}`
   per Step 3's instruction (fix the fixture, don't weaken the assertion) — this is the same class of
   error task 10's report recorded for its own Step 7 fixture, now recurring for the same block in a
   different task.
2. **`sweep.ablate`'s brief-given shape is wrong the same way.** The brief's fixture used
   `"ablate": [{"remove": ["llm.provider"]}]` — a list. `sweep.py`/`docs/reference.md` define
   `sweep.ablate` as a single **mapping** with a `remove` (and optional `from`/`override`) key, e.g.
   `ablate: {remove: [...]}`. Run verbatim, this also earns `E-CONFIG-SHAPE`/`E-CONFIG-TYPE`.
   Corrected to `"ablate": {"remove": ["llm.provider"]}`.
3. **The brief's Step 4 guidance to pin the setdefault/assignment mutation "in the paired fixture"
   does not hold up against the code.** The paired fixture has no attribution race for that mutation
   to affect (see above); the groups fixture does, and that is where the pinning assertion actually
   belongs and actually discriminates. Recorded here rather than silently moved, per this slice's own
   convention of naming every disagreement.

Both shape corrections were caught by Step 2's mandated diagnostic step (`expand(...)` / running the
config and reading the actual findings) rather than by assuming the brief's YAML was correct — the
same discipline `CLAUDE.md` names under *"Assuming a documented rule has code behind it"* and under
the H3c/H7a lesson to check the code, not the brief's prose, before trusting a shape.

## Review round — two findings against the first draft, both fixed

A pre-completion review of this task's own test code found two defects in the *test* prose/assertion
shape, not in `validate.py`:

1. **`messages_by_code` cannot see a duplicate finding.** It is `{f.code: f.message for f in
   c.findings}` — same-code findings collapse last-wins. The baseline and paired tests originally
   asserted through `messages_by_code(path)["E-CRED-PARAM-MISSING"]` and then commented that the
   absence of the other variable's name was "the positive companion that keeps this from being an
   absence-only control" — but a spurious *second* finding for the already-set key would be
   invisible to that lookup (in the paired case, insertion order is the azure cell then the ollama
   cell, so a wrongly-doubled report would keep ollama's message and both assertions would still
   pass over a hidden extra finding). Fixed by switching both tests to `_findings_of` with an
   explicit `assert len(found) == 1, [...]` before the membership assertions — the same shape the
   groups and ablate tests already used.
2. **The groups test's comment overclaimed uniqueness and misdescribed the paired fixture.** It said
   this was "the one attribution race this file's fixtures carry," but task 10's own
   `test_a_variable_two_conditions_need_is_reported_once` carries the identical race for `grid`
   (proven directly above, where that test is what actually fails under the
   `first_seen[...] = ...` mutation). It also said the paired fixture's "two paths need two
   different variables," which is wrong on its face — `llm.retries` carries no `requires_env` at
   all, so only one of the paired fixture's two paths carries a credential requirement in the first
   place. Rewrote the comment to state only what the code and the other tests actually establish.

Both fixes verified by re-running the full `test_validate.py` (696 passed) and the full suite (1989
passed, 2 xfailed) after each edit, and by re-running the prescribed `conditions[:1]` mutation
against the corrected paired test (see above).

## Concerns

None outstanding. All four gate commands are clean. `_check_requires_env`, as task 10 wrote it,
already generalizes correctly across `baseline`, `paired`, `groups`, and `ablate.remove` with zero
production changes needed — the only work this task did was proving that generalization with
fixtures shaped to match the real schemas, finding that one of the four tests (paired) needed no
extra pinning while a different one (groups) needed an assertion the first draft mis-assigned, and
then catching two prose/assertion defects in its own first draft on review (above).

`git checkout -- .superpowers/sdd/.gitignore` was used once during this task to restore that file
after it turned up clobbered to a bare `*` (the `scripts/sdd-workspace`/`task-brief` hazard
`CLAUDE.md` names) — not against any mutation of mine, and `git diff` before the checkout confirmed
the clobbered content had nothing worth preserving beyond the tracked comment block itself, which the
checkout restored verbatim.

`.superpowers/sdd/2026-08-16-credentials-and-secrets/task-N-report.md` files are **tracked** —
confirmed via `git ls-files` against task 1 through task 10's reports, all present — so this report
is committed with `git add -f` (needed because the clobbered-then-restored `.gitignore` episode above
left no residual ignore rule against it, but `-f` is the belt-and-braces `CLAUDE.md` recommends for
any new record in this directory).
