# Task 3 report: `Param(requires_env=)` — the constructor argument

**Status:** Complete. All steps 1–8 executed as specified in the brief.

**Commit:** will be created immediately after this report is written (see below for the
message); this file records the pre-commit working tree at parent `e3ac3a475f3e8b2e81dbb63f9459a51bfedecfea`.

**Test summary:** `uv run pytest -q` → **1962 passed, 2 xfailed** (1957 baseline + 4 new
`test_param.py` tests + 1 new `test_validate.py` end-to-end test). `uv run ruff check .`,
`uv run ruff format --check .` (74 files formatted), and `uv run mypy` (42 source files) are
all clean.

## Task 2's forward-referencing comment: confirmed true

`grep -rn "requires_env" src/publishable/` before this task returned exactly one hit —
`validate.py`'s comment asserting that a `requires_env` mapping not total over `choices` is a
`Param`-construction fault surfacing as `E-TEMPLATE-LOAD`. After this task, the same grep
returns nine hits in `param.py` (the docstring addition, the parameter, the two checks, the two
message-building expressions, and the stored attribute) plus the original `validate.py`
comment, now true rather than aspirational.

I confirmed it two ways:
1. **Directly**: `Param(str, default="a", choices=["a","b","c"], requires_env={"a": [...], "b": []})`
   now raises `ValueError` naming both the `choices` set and the `requires_env` keys, with the
   missing/extra-key detail clauses separately present.
2. **End-to-end**, per Step 5: `test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding`
   writes a `templates/cred_assay.py` declaring a partial `requires_env`, runs `write_config`
   (which drives `validate_config` → `resolve_template` → `discover_local`), and asserts the
   finding lands under `E-TEMPLATE-LOAD` with the `ValueError(...)` repr embedded (per `{exc!r}`
   in `discovery.py`), not under `E-CRED-MISSING` or `E-CRED-PARAM-MISSING`. This test passes
   with the Step 3 implementation in place and needed no changes to `validate.py` or
   `discovery.py` — the route task 2 asserted was already correct, this task only had to make the
   raise exist.

## Step 6 mutations — exact text and outcome

**(a) Delete the `if absent or extra:` block entirely.**
- `test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets`: **FAIL**
  — `Failed: DID NOT RAISE ValueError` at its first `pytest.raises(ValueError) as short:` block
  (`tests/test_param.py:117`).
- `test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding`: **FAIL**
  — `KeyError: 'E-TEMPLATE-LOAD'` at `message = found["E-TEMPLATE-LOAD"]`
  (`tests/test_validate.py:12266`).
- Reverted by hand, re-ran `tests/test_param.py::test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets`
  and the validate test: both **PASS**. `diff` against the pre-mutation copy: identical.

**(b) Change `if absent or extra:` to `if absent:`.**
- `test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets`: **FAIL**
  — the first `pytest.raises` block (missing-key case) still passes; **FAIL** at the second
  `with pytest.raises(ValueError) as extra:` block — `Failed: DID NOT RAISE ValueError`
  (`tests/test_param.py:130`), because the unknown-key fixture (`choices=["a","b"]` fully keyed
  plus `"zz"`) makes `absent` empty and only `extra` would have caught it.
- Reverted by hand, re-ran: **PASS**. `diff` against the pre-mutation copy: identical.

**(c) Delete the `if choices is None: raise ...` guard.**
- `test_requires_env_is_stored_and_needs_choices`: **FAIL** — but as a `TypeError`, not
  `DID NOT RAISE`: `TypeError: 'NoneType' object is not iterable` at
  `absent = [c for c in choices if c not in requires_env]` (`src/publishable/param.py:57`),
  because `pytest.raises(ValueError, match="choices")` propagates the uncaught `TypeError`
  rather than reporting `DID NOT RAISE`. This is the exact shape the brief calls out and asks to
  distinguish from a transcription error — confirmed correct here since the guard in Step 3 is
  a `raise`, ordered before the list comprehensions, exactly as specified.
- Reverted by hand, re-ran: **PASS**. `diff` against the pre-mutation copy: identical.

All three reverts were verified both by `diff` against a copy of the file saved before mutating
and by re-running the named tests — never by `git status`. `__pycache__` was cleared between
each mutation and revert.

## Step 7 — the deliverable no mutation reaches

Per the brief: `self.requires_env` being *stored* is pinned only by the two reads inside
`test_requires_env_is_stored_and_needs_choices` (dropping the assignment gives
`AttributeError`, not tested by a dedicated mutation here). `_joined`'s output order is not
independently pinned — it follows `choices`'s declared order, and every fixture declares
`choices` already sorted, so a mutation that reordered `_joined`'s internals would not be caught.
This is deliberate: the order belongs to `choices`, not to `_joined`, and a fixture built to
separate them would only be pinning `list` iteration order, not this function's behavior.

## Where the brief/spec disagreed with the code

None found. `param.py`'s file-level names (`MISSING`, `_TYPE_NAMES`, `Param`), the
`Param.__init__` signature (twelve keyword-only args before this task), the precedent at line 34
(`ValueError("default=None requires nullable=True")`), `test_validate.py`'s module-level names
(`base_config`, `write_config`, `codes`, `messages_by_code`, `_validate_with`, `_error_codes`,
the `_*_EXPERIMENT` constants), and `discovery.py`'s `except Exception as exc:` /
`{exc!r}` interpolation at `src/publishable/templates/discovery.py` all matched the brief's
description exactly, including the file's actual path being
`src/publishable/templates/discovery.py` rather than a bare `discovery.py` (the brief's prose
uses the short name informally but never asserts a path). The Step 2 claim that "every new test
must fail with `TypeError`" was slightly imprecise for
`test_a_param_without_requires_env_reports_none_rather_than_an_empty_mapping`, which does not
pass the `requires_env` keyword at all and so failed with `AttributeError:
'Param' object has no attribute 'requires_env'` instead — a cosmetic overstatement in the brief's
summary sentence, not a defect in the test or the implementation; the test's own body needs no
correction.

`ruff format` reformatted three trailing-comment lines in the Step 1 test bodies (collapsing
inline `# comment` alignment to single-space) and reflowed the two-line `Param(...)` call in
`test_a_total_requires_env_constructs_and_leaves_every_other_check_alone` to one line, and two
lines in the Step 5 test to satisfy the repo's 74-file format-clean gate. Text content and all
assertions are otherwise verbatim from the brief.

## Concerns

None outstanding. The implementation, docstring amendment, and tests are exactly as specified;
the closed-constraint-vocabulary invariant is preserved by the docstring explanation rather than
by widening `docs/reference.md` § Templates' table. Task 4 can now consume `self.requires_env`,
and tasks 10/11 can gate on its truthiness through `template.parameter_spec`.
