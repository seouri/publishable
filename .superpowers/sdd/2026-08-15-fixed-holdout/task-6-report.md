# Task 6 report — `_check_holdout` declaration half B: `stratify_by` existence, `holdout` × `fold`

**Status:** DONE

**Commit:** (to be filled after commit)

**Test summary:** `uv run pytest` → 1857 passed, 2 xfailed (baseline 1847 + 10 new). `uv run ruff check .` clean. `uv run mypy` clean. `uv run ruff format --check .` shows only the pre-existing ~68-file standing baseline plus one line in my own appended test code that reproduces the brief's literal fixture text verbatim (`overrides["replication"] = {...}` on one line) — not reformatted, per the "never run ruff format bare" instruction and since the brief's code block is to be used verbatim.

## What was built

Extended `_check_holdout` in `src/publishable/validate.py` with:
- `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` — reads `stratify_by` through `units.stratum_names` (never a hand-rolled `isinstance` chain), reports one finding per offending name against three faults: not a string / empty, not a declared `data.units.attributes` name, or equal to `data.units.measurements.by` (the consumed measurement axis).
- `E-DATA-HOLDOUT-FOLD` — the only check in `_check_holdout` reading a block other than `data.units`: refuses `data.units.holdout` declared beside a `{kind: fold}` repeat level in `doc["replication"]["repeats"]`.

Docstring's enumeration grown from five to seven, matching the brief's given text (with "None of the five reads..." now "Only `E-DATA-HOLDOUT-FOLD` reads `doc`...", since task 6 is what makes the previously-dead `doc` parameter live).

Appended 7 new tests (10 test functions counting the `@pytest.mark.parametrize` with 4 cases) to `tests/test_validate.py`, taken from the brief verbatim, **except one test I strengthened — see Disagreement below.**

## Disagreement with the brief: Step 5(a)'s mutation does not fail as claimed

The brief (and the controller's "Verified before dispatch" note) asserted that Step 5(a)'s prescribed mutation —

```python
strata = tuple(raw_strata) if isinstance(raw_strata, list) else ()
```

— **must FAIL** `test_a_bare_string_holdout_stratum_is_read_as_one_name` (`-k bare_string_holdout_stratum`).

I ran it. **It PASSED.** Root cause: the test as given only asserts a *count* —

```python
assert len([f for f in c.findings if f.code == "E-DATA-HOLDOUT-STRATIFY-UNKNOWN"]) == 1
```

Under the mutation, `raw_strata = "sexes"` is a `str`, not a `list`, so `strata = ()`. That makes `raw_strata is not None and not strata` true, firing the *empty* branch's `c.error(...)` exactly once — a different branch, a different message ("is empty, which names no attribute...") from the correct behaviour's ("names 'sexes', which is not a unit attribute..."), but **the same count: 1.** The test cannot tell the two branches apart because it never reads the message — this is precisely the CLAUDE.md "A dimension no assertion can see" / message-blind shape the repo's own history warns about.

I verified this directly (calling `_check_holdout` with the mutation applied, printing `c.findings`): one finding, code `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`, message `"is empty, which names no attribute..."`.

**Fix applied:** strengthened the test to also assert on the message —

```python
unknown = [f for f in c.findings if f.code == "E-DATA-HOLDOUT-STRATIFY-UNKNOWN"]
assert len(unknown) == 1
assert "'sexes'" in unknown[0].message and "is not a unit attribute" in unknown[0].message, (
    unknown[0].message
)
```

I added a docstring paragraph explaining why the message must be checked. Re-ran with the mutation applied: now **FAILS** with the wrong message reported. Reverted the mutation, re-ran: passes with the correct message. This is the only place I diverged from the brief's literal test text.

Mutation 5(b) (retargeting the fold exclusion from `"fold"` to `"batch"`) behaved exactly as the brief predicted: `test_a_holdout_beside_a_fold_repeat_is_refused` failed cleanly (`E-DATA-HOLDOUT-FOLD` missing from the found set) under the mutation, and passed again after reverting.

## `docs/reference.md` — no change needed

Grepped § Errors for both new codes. Both rows already exist (lines 482–483 at HEAD) and their prose already matches what the code does — including the three-way `stratify_by` fault enumeration and the `holdout`/`fold` mutual-exclusion wording. Task 1 minted these correctly; nothing to update.

## Process notes

- `.superpowers/sdd/.gitignore` was clobbered to a bare `*` by the `task-brief` tooling run that produced this task's brief (per CLAUDE.md's documented standing bug). Restored its tracked content from `HEAD` before committing.
- No `git checkout --` was used; all reverts during mutation testing were by editing the file back in place and re-running the named test to confirm behaviour, never by `git status`.
- `__pycache__` cleared between mutation runs.

## Concerns

None outstanding. The one disagreement (mutation 5(a) not discriminating as claimed) was resolved by strengthening the test rather than papering over it — the underlying implementation was correct throughout; only the test's assertion was too weak to prove it.
