# Task 2 report

## Status: complete

## Counts measured (Step 1)

**`validate.py`'s `except ContractError` guard (line 518, inside `validate_config`):** exactly
**two codes** can arrive there. `resolve_template` is the only call inside the `try`. Traced both
raise sites it can reach:
- `templates/registry.py`'s `_merged` raises `code="E-TEMPLATE-COLLISION"` (one raise site, line 44).
- `templates/discovery.py`'s `discover_local`, which `_merged` calls, raises `code="E-TEMPLATE-LOAD"`
  at four sites (lines 313, 331, 341, 359 — `sys.exit()`, a coded or uncoded raise while importing,
  never calling `@register_template`, and registering a non-`BaseTemplate`) and `code="E-TEMPLATE-COLLISION"`
  at one more (line 398, the same code as `registry.py`'s).

No other code is raised on this path. **Two codes confirmed.**

**`reference.md`'s early-return paragraph (§ Errors `validate` reports, line 429):** enumerated the
five faults named: `E-CONFIG-PARSE`, container-shaped `E-CONFIG-SHAPE`, `E-TEMPLATE-LOAD`,
`E-TEMPLATE-COLLISION`, `E-TEMPLATE-UNKNOWN`. **Five codes confirmed**, matching the five distinct
`return None` sites walked in `validate_config` (parse failure, shape failure, the `except`
clause's two codes, and the unresolved-name branch).

Both counts stay as predicted: neither enumeration grows, because a `Param` construction fault
(`default=None` without `nullable=True`, or a non-total `requires_env` mapping) is reported as
`E-TEMPLATE-LOAD`'s existing "raises while importing" shape, not a new code.

## Verification of the two new H7c rows (not in the brief's step list, checked on advisor's flag)

Read the two rows task 1 inserted at `docs/reference.md` lines 470–471. `E-CRED-MISSING` is a
template-level `required_env` check (an unset env var for the resolved template); `E-CRED-PARAM-MISSING`
is a parameter-value-level check (an unset env var for a `requires_env` value the sweep actually
resolves). Neither row's condition is "the `requires_env` mapping is not total over `choices`" —
that totality fault is confirmed by `E-CRED-PARAM-MISSING`'s own closing sentence ("`requires_env`
is total over `choices`") to be enforced elsewhere, at `Param` construction, which raises before
either new code's check runs. So the sentence added to `reference.md`'s early-return paragraph is
correct: a `Param` construction fault is `E-TEMPLATE-LOAD`, not either new code.

## Edits

- `src/publishable/validate.py`: comment above the `except ContractError` guard reworded from
  "two today" to "two codes", with the codes-vs-faults distinction spelled out (per Step 2 exactly).
- `docs/reference.md`: one sentence inserted into the early-return paragraph after the five-fault
  enumeration, before "Each returns because…" (per Step 3). Also reflowed that pre-existing sentence
  from two lines to one while inserting — cosmetic, no wording changed, noting it since the task
  didn't ask for it.

## Step 4 sweep

`grep -rn "E-TEMPLATE-LOAD" src/publishable/` (whole tree, not just `discovery.py`) and
`grep -n "E-TEMPLATE-LOAD" docs/reference.md` (whole file). Hits: `discovery.py` (docstring lines
252/259, code sites 313/331/341/359, and the relabeling-comment lines 321/323), `validate.py`'s own
edited comment, and in `reference.md`: the two § Errors table rows (line 570 `validate`-reports
table, line 1009 `ContractError`-raises table), § Templates' "Every non-dunder-stemmed file under
`templates/` is a template" paragraph (line 3416), and the `requires_env` paragraph (line 1635,
which already states the Param-fault-is-E-TEMPLATE-LOAD relationship task 1 wrote). All already
read generically ("raises while importing" / "raises on import" already covers a `Param`
construction fault) — none needed changing.

## Test summary

`uv run pytest`: 1957 passed, 2 xfailed (unchanged). `uv run ruff check .`: all checks passed.
`uv run ruff format --check .`: 74 files already formatted. `uv run mypy`: no issues found in 42
source files.

## Concerns / disagreements found

None with the brief or spec. The brief's prediction ("both counts stay as they are") was confirmed
by direct enumeration, not assumed.
