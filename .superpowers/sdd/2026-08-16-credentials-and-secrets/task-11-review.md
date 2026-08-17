# Task 11 review: the expansion modes the union must cover

**Verdicts:** Spec compliance ✅ · Task quality ✅

Everything below was verified by running it. `src/publishable/validate.py` was copied to the
scratchpad before every mutation and restored by copying back (never `git checkout --`);
`__pycache__` deleted and the suite re-run after each revert. Final tree: `uv run pytest` 1989
passed + 2 xfailed, `ruff check` clean, `ruff format --check` 76 formatted / 0 to reformat, `mypy`
clean over 43 files. `git status` shows only the pre-existing `.superpowers/sdd/.gitignore`
modification.

## The `messages_by_code` last-wins question

**Verified.** `tests/test_validate.py:139` is `{f.code: f.message for f in c.findings}` — same-code
findings collapse, last wins.

**Count: 4 message-pinning `messages_by_code` sites were written across this slice's history. 2 were
genuinely weakened — both in task 11, both found and fixed by the implementer in `fc093e0` before
the final commit, so they no longer exist as call sites. The 2 that remain are not weakened, and
none is vacuous.** Evidence: `git merge-base main HEAD` = `878a862`; `git diff $B..HEAD -- tests/`
over all five touched test files (`conftest.py`, `test_cli.py`, `test_param.py`, `test_secrets.py`,
`test_validate.py`) adds four lines containing the string — **two call sites** (the two below) and
**two explanatory comments** written by task 11 about the last-wins behaviour itself. The converted
pair is absent from that net diff precisely because it was converted. The other 44 of the file's 48
occurrences predate this slice and are out of this task's scope.

The two survivors, with the reasoning rather than just the verdict:

| Site | Code pinned | Why it is structurally single-finding |
|---|---|---|
| `test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding` (~12263) | `E-TEMPLATE-LOAD` | Emitted **per file** in `templates/discovery.py`, and each of its four branches `continue`s, so one file yields at most one finding. The fixture's `templates/` holds exactly one file. Its other two assertions are `not in` over the dict's **keys**, which last-wins cannot affect |
| `test_an_undeclared_parameter_falls_back_to_the_template_s_default` (~12499) | `E-CRED-PARAM-MISSING` | No `sweep` → one condition; one credentialed path in `wanted`; `azure_openai` maps to one variable. At most one finding. Checked the adversarial case too: a report-over-all-`choices` mutant emits three findings and last-wins keeps ollama's, so `"AZURE_TEST_KEY" in message` still reddens |

Both plural-by-design codes are pinned elsewhere by **counted** assertions, not by `messages_by_code`:
`E-CRED-MISSING`'s two-variable test (~12343) and every `E-CRED-PARAM-MISSING` test at 12458, 12524,
12601, 12658, 12685, 12721, 12761 use `[f for f in c.findings if f.code == ...]` with a `len(...)`
assertion. **So this is not an Important finding against the slice** — no other task owns a weakened
assertion.

## Findings

### Minor 1 — the groups test's docstring claims a guarantee the fixture does not provide

`tests/test_validate.py` `test_a_groups_axis_contributes_no_parameter_value` docstring: *"The roster
is rewritten first: … `attributes: ["cohort"]` over that file earns `E-UNITS-ATTR-MISSING` and this
test would pass for the wrong reason."*

**Verified false by deletion.** Removing the `(tmp_path / "input" / "index.csv").write_text(...)`
line leaves all four assertions — including `condition \`cohort=derivation\`` — passing unchanged; I
then printed the code set from inside the test and got
`['E-CRED-PARAM-MISSING', 'E-DATA-ALLOCATION-WITHIN-ARMS', 'E-UNITS-ATTR-MISSING']`. The extra
finding appears exactly as the docstring predicts, but **no assertion reads it**, and `expand` is
document-only (`sweep.groups` yields its two labelled cells regardless of the roster), so the test
passes for precisely the same reason with or without the rewrite. The rewrite is fixture hygiene —
worth keeping — but the docstring's "would pass for the wrong reason" is the `CLAUDE.md` *(b)*
shape: a comment asserting a guarantee the code does not provide. Restored the line; re-ran green.

### Minor 2 — a comment the review round's own fix falsified

Paired test, after the `_findings_of` conversion:

```python
    # Azure's key IS set, so the union reports one variable and not two — the
    # positive companion that keeps this from being an absence-only control.
    assert "AZURE_TEST_KEY" not in found[0].message
```

The sentence attributes the anti-absence property to an **absence** assertion. Since the review
round, what actually carries it is `assert len(found) == 1` two lines above (and, positively,
`"OLLAMA_TEST_KEY" in found[0].message`). The comment is pre-fix residue that survived the fix it
describes. The baseline test's equivalent comment is accurate and needs nothing. Same family as
Minor 1; neither weakens a test.

Related, not a separate finding: the emit site writes one variable per message, so with
`len(found) == 1` pinned the two `not in` assertions are near-redundant. They are not *vacuous* —
a mutant that resolved only the last condition's value would yield one finding naming the wrong
variable — so they earn their place, just not the rhetorical weight the comment gives them.

### Minor 3 — the report under-claims its own coverage (Step 5)

The report states no single-line mutation reddens
`test_ablate_remove_resolves_a_value_with_no_key_and_requires_nothing`. **There is one, it is the
realistic slip, and I ran it:** in `_check_requires_env`, `if path in resolved:` →
`if resolved.get(path) is not None:` — i.e. treating a resolved `null` as absent and falling back to
`param.default`. The ablated condition then resolves `azure_openai`, which is unset, and the test
fails `assert 2 == 1` with both messages shown. **Only that test failed**; the other three passed,
so the ablate fixture is the unique guard for the "legal resolved value with no key" property.
Reverted; re-ran green. The deliverable is therefore *covered by mutation*, not merely by count —
a correction that strengthens the record rather than weakening it.

### Minor 4 — `.superpowers/sdd/.gitignore` was clobbered again after the report claimed it restored

The report records restoring that file during task 11. It was a bare `*` again at review time —
`git check-ignore -v` showed this review file itself being ignored by it. Restored from `HEAD` (its
committed content is intact; the working copy held nothing but the clobber). The report's
"restored verbatim" is true of the moment it was written and no longer true of the tree, which is
the hazard `CLAUDE.md` names: **check it at the end of a task as well as the start.** The `E-CRED`
row citation in the report — `E-DATA-ALLOCATION-WITHIN-ARMS` → § Validation *Arms need allocation* —
was checked and **is** the row's name (`reference.md` § Validation, and the § Errors row for that
code cites the same name).

### Minor 5 — a Step 3 deviation, defensible and declared

The brief says "if a fixture earns an unrelated error, fix the fixture — do not weaken the
assertion." The groups fixture keeps `E-DATA-ALLOCATION-WITHIN-ARMS` and attributes it in the report
rather than adding `allocation: between`. Defensible: every assertion is membership over a filtered
list, never set equality, so nothing was weakened to accommodate it. Recorded here so the deviation
is not silent.

## Checks that came back clean

**The four modes are genuinely four.** Ran `expand()` on all four documents:

| Fixture | `expand` output |
|---|---|
| baseline | 4 conditions; `00 retries=1__baseline` and `01 retries=2__baseline` carry `is_baseline=True` and `llm.provider: openai`; `02`/`03` carry no provider |
| paired | exactly 2 conditions (not a 2×2 product): `provider=azure_openai__retries=1`, `provider=ollama__retries=4` |
| groups | 2 conditions whose only value is `cohort`, and `selectors == {"cohort"}` — no parameter path at all |
| ablate | `00 baseline` (`provider: openai`) and `01 provider=None` — the nullable target resolved to `None` |

**The two shape corrections are the real schema.** `sweep.py:502` states outright that `groups` is
"a **list**, always … there is no mapping shorthand", and `_axes` reads `sweep.get("groups") or []`
as entries with `by`/`levels`; `ablation_changes` (sweep.py:625) returns `[]` unless
`isinstance(ablate, dict)` and iterates its `remove`/`override` keys. `reference.md` § Expansion
modes' `ablate × groups` example shows both shapes verbatim. Report disagreements 1 and 2 are
correct as written.

**Every mutation claim in the report reproduces.**

| Mutation | Result |
|---|---|
| `conditions[:1]` | **paired only** fails; baseline, groups, ablate blind — exactly as reported |
| `if condition.is_baseline: continue` | **baseline and ablate** fail (`found == []`); paired and groups pass. `Condition.is_baseline` is a real field (`sweep.py:48`), so the report's empirically-found mutation is one it could and did run |
| `first_seen.setdefault(...)` → `first_seen[...] = ...` | **groups** and task 10's `test_a_variable_two_conditions_need_is_reported_once` both fail — the added `condition \`cohort=derivation\`` assertion is load-bearing, and the report's correction of the brief (pin it in groups, not paired) is right: the paired fixture has one requiring condition and no attribution race |

**`ablate.remove` requires nothing, and for the right reason.** All three `_UNION_NAMES` are
`delenv`-ed in that test, so nothing passes by a variable happening to be set — proven by the Minor 3
mutation, which flips the same fixture to two findings the moment the `None` stops being honoured.
The mechanism is `param.requires_env.get(None)` → `None` over a mapping total on `choices`.

**No reachability assumption.** `validate` collects; the groups fixture demonstrates it directly by
carrying an unrelated error *and* the credential finding on one document. No test in this task
assumes a config is "refused so the check doesn't run", and every assertion filters by
`f.code == ...` rather than comparing code sets — the one `== set()` in the region is task 10's
honouring test, where equality is meant.

**Environment hygiene.** No new autouse fixture; the slice's only one is task 8's `_restore_environ`
in `tests/conftest.py`. `_union_project` `delenv`s all three names and `setenv`s only `set_names`, so
both directions are exercised; the ablate test does its own `delenv` loop because it needs the
nullable template variant. Every negative has a positive on the same document (baseline/paired: the
set key is silent while the unset one reports; ablate: the baseline condition still reports; groups:
the base value's requirement reports).
