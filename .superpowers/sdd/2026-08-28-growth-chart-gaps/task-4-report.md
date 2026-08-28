## Task 4 — `E-TEMPLATE-PARAM-PATH` at template load

**Status:** done.

**Ruling honoured, mechanism overruled with cause.** The ruling said "beside the sibling
`Param` validation, in the same style, raising the same way" (i.e. `Param.__init__`'s bare
`ValueError` for `default=None`). That mechanism turned out to be unreachable as a standalone
identifier: `discovery.py`'s `except Exception` unconditionally relabels *any* raise from a
project-local template's import to `E-TEMPLATE-LOAD` (its own docstring says so), and
`reference.md`'s existing text says a `Param`-construction raise "adds a shape to
`E-TEMPLATE-LOAD` ... without adding ... a code to this set" — the opposite of "mint a code."
`Param` also cannot check this itself: the path is the *caller's* dict key, never passed to
`Param.__init__`. Checked further: `list-templates` (`docs.template_details`) reads
`claim.cls.parameter_spec` straight off the **class**, never instantiating — so a check placed
only in `__init__` would leave that surface (named in the ruling's own grounds) silent.

Landed instead in `BaseTemplate.__init_subclass__` (`src/publishable/templates/base.py`) —
fires at class-*definition* time, before `@register_template` runs, covering every surface
that resolves a template (`validate`, `generate experiment`, `list-templates`, `freeze`,
`report`, `reproduce`, `demo`) from one site, with no other call site touched. For a
project-local template it still folds into `E-TEMPLATE-LOAD`'s "raises while importing" shape
for the same reason nullable's does — but the message embeds the literal string
`E-TEMPLATE-PARAM-PATH`, so it stays legible inside `E-TEMPLATE-LOAD`'s `{exc!r}`. Guarded
against a non-`dict` `parameter_spec` (skip rather than iterate) to match the existing
convention in `validate.py` ("not this collector's crash to cause") and to avoid changing an
unrelated pre-existing test that pins that different fault.

`materialize._parameters_block`'s `ValueError` guard stays, docstring updated to say it is now
unreachable through any real template and why (`__init_subclass__` runs first).

**Docs:** `reference.md` § Errors `validate` reports gained the row (alphabetical position,
between `E-TEMPLATE-LOAD` and `E-TEMPLATE-RULE`); § Templates gained a paragraph beside the
three-states table stating the constraint; the "There is no `dict` type" sentence was narrowed
("one level of it... never zero or more than two") since it read as permitting arbitrary depth.

**Tests:** two new tests in `tests/test_templates.py`
(`test_a_one_segment_parameter_spec_path_is_a_diagnostic_not_a_traceback`,
`test_a_three_segment_parameter_spec_path_is_also_refused`), through `discover_local` — the
real surface, not the helper directly.

Mutation evidence (`path.count(".") != 1` replaced with `if False:` in
`src/publishable/templates/base.py`, then reverted):

RED —
```
$ uv run pytest tests/test_templates.py -k "one_segment_parameter_spec_path or three_segment_parameter_spec_path" -q
...
E       Failed: DID NOT RAISE ContractError
...
FAILED tests/test_templates.py::test_a_one_segment_parameter_spec_path_is_a_diagnostic_not_a_traceback
FAILED tests/test_templates.py::test_a_three_segment_parameter_spec_path_is_also_refused
2 failed, 47 deselected in 14.32s
```

GREEN (reverted, `cp /tmp/base.py.bak src/publishable/templates/base.py`) —
```
$ uv run pytest tests/test_templates.py -k "one_segment_parameter_spec_path or three_segment_parameter_spec_path" -q
..                                                                       [100%]
2 passed, 0.50s
```

A second, independent red also surfaced honestly during development rather than by mutation: the
one-segment test's original `assert "E-TEMPLATE-PARAM-PATH" in message` failed the first time it
ran (before the message embedded the literal code string), with
`assert 'E-TEMPLATE-PARAM-PATH' in '...renaming it to `"frame.reference"`.\')'` — proof that the
code string does not travel through `repr()` on its own, which is why the raise message now
embeds `E-TEMPLATE-PARAM-PATH:` literally.

Two **pre-existing** tests broke as a direct, expected consequence and were updated:
`test_a_non_two_segment_parameter_path_fails_loudly` (pinned the now-unreachable
`materialize.ValueError` path — rewritten to call `_parameters_block` directly) and
`test_validate_reports_rather_than_raises_on_a_partial_template_with_a_malformed_parameter_spec`
(a `parameter_spec = "not-a-dict"` fixture — fixed by the `isinstance(..., dict)` guard above,
no longer touched, test now passes unchanged in assertions).

**Commands** (final run, against commit to be made):
- `uv run pytest -q` — 3487 passed, 1 skipped, 2 xfailed in 415.03s (baseline 3485 passed; the
  delta is exactly the two new tests)
- `uv run ruff check .` — All checks passed!
- `uv run ruff format --check .` — 101 files already formatted
- `uv run mypy` — Success: no issues found in 56 source files

**Concerns:** `freeze.py`'s `claim.cls()` call (line ~277) is not wrapped in a try/except the
way `_claims()` above it is — a pre-existing gap (unrelated to this task) that would now let an
`E-TEMPLATE-PARAM-PATH`-raising **core** template escape un-redacted if one ever existed; not
reachable for a project-local template, since `__init_subclass__` fires during `discover_local`'s
own already-wrapped import. Did not touch `freeze.py`, out of this task's scope. Also did not
add a row to § Errors core raises (task named only § Errors `validate` reports).
