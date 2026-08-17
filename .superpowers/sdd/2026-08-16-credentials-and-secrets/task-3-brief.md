## Task 3: `Param(requires_env=)` — the constructor argument · **the H7b prerequisite**

**Files:** Modify `src/publishable/param.py`, `tests/test_param.py`.

**Interfaces:**
- Consumes: `Param.__init__(self, type_: type, *, default: Any = MISSING, choices: list[Any] | None
  = None, ge, gt, le, lt, pattern, item_type, min_items, max_items, nullable: bool = False,
  help: str | None = None) -> None` — twelve keyword-only arguments today, at
  `src/publishable/param.py`, read from that file.
- Produces: a thirteenth, `requires_env: dict[Any, list[str]] | None = None`, stored as
  `self.requires_env`; a `ValueError` naming both sets when it is not total over `choices`; a
  `ValueError` when `choices` is absent. **Task 4 consumes `self.requires_env`; tasks 10 and 11
  consume it through `template.parameter_spec`.**

**Why this is the prerequisite.** The feasibility analysis's `llm_screen` template declares
`Param(..., requires_env=…)` at module scope. `Param.__init__` rejects that keyword today
(`TypeError: Param.__init__() got an unexpected keyword argument 'requires_env'`, probed by the
scoping), so the plugin H7b's registry would resolve **cannot be written** until this lands. Nothing
else in H7c gates this task.

**Names already at module level in `src/publishable/param.py`:** `MISSING`, `_TYPE_NAMES`, `Param`.
`_joined` is free. **Names already at module level in `tests/test_param.py`:** the ten `test_*`
functions and nothing else — no helpers, no constants. Any helper you add is new.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_param.py`:

```python
def test_requires_env_is_stored_and_needs_choices():
    """The keyword `Param.__init__` rejects today. `choices` is required because a
    credential requirement is only checkable when the value set is closed —
    `reference.md` § A credential can belong to a parameter value."""
    p = Param(
        str,
        default="azure_openai",
        choices=["azure_openai", "openai", "ollama"],
        requires_env={
            "azure_openai": ["AZURE_OPENAI_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "ollama": [],
        },
    )
    assert p.requires_env["openai"] == ["OPENAI_API_KEY"]
    assert p.requires_env["ollama"] == []  # `[]` is a claim, not an omission

    with pytest.raises(ValueError, match="choices"):
        Param(str, default="a", requires_env={"a": ["A_KEY"]})


def test_a_param_without_requires_env_reports_none_rather_than_an_empty_mapping():
    """`None` and `{}` are different claims — the first is "this parameter declares
    nothing", the second would be "every choice needs nothing", which is only
    legal for an empty `choices`. Tasks 10 and 11 gate on truthiness, so the
    distinction is load-bearing rather than cosmetic."""
    assert Param(str, default="a", choices=["a", "b"]).requires_env is None


def test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets():
    """Both directions, each with its own distinguishing fragment.

    `reference.md` § A credential can belong to a parameter value requires the
    message to name *both sets*; the direction clause is what makes the two
    branches separately pinnable, since both raise `ValueError` and both surface
    to a user as one `E-TEMPLATE-LOAD`.
    """
    with pytest.raises(ValueError) as short:
        Param(
            str,
            default="a",
            choices=["a", "b", "c"],
            requires_env={"a": ["A_KEY"], "b": []},
        )
    text = str(short.value)
    assert "choices are a, b, c" in text          # both sets named
    assert "requires_env names a, b" in text      # both sets named
    assert "no key for c" in text                 # only the missing-key branch says this
    assert "naming no choice" not in text         # and only that branch

    with pytest.raises(ValueError) as extra:
        Param(
            str,
            default="a",
            choices=["a", "b"],
            requires_env={"a": ["A_KEY"], "b": [], "zz": ["Z_KEY"]},
        )
    text = str(extra.value)
    assert "choices are a, b" in text
    assert "requires_env names a, b, zz" in text
    assert "keys naming no choice: zz" in text    # only the unknown-key branch
    assert "no key for" not in text

    # Both directions at once, in one message: the fault a real edit makes when a
    # choice is renamed. Neither clause may swallow the other.
    with pytest.raises(ValueError) as both:
        Param(str, default="a", choices=["a", "b"], requires_env={"a": ["A_KEY"], "zz": []})
    text = str(both.value)
    assert "no key for b" in text
    assert "keys naming no choice: zz" in text


def test_a_total_requires_env_constructs_and_leaves_every_other_check_alone():
    """The honouring. Without it, ignoring `requires_env` entirely — storing it and
    checking nothing — passes every refusal test above."""
    p = Param(str, default=None, nullable=True, choices=["a", "b"],
              requires_env={"a": ["A_KEY"], "b": []})
    assert p.check("a") is None
    assert p.check("zz") is not None
    assert p.check(None) is None
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest tests/test_param.py -q`. Every new test must
      fail with `TypeError: Param.__init__() got an unexpected keyword argument 'requires_env'`.
      A failure of any other shape means the argument already exists and this brief is stale.

- [ ] **Step 3: Implement.** In `src/publishable/param.py`:

Amend the module docstring, whose "closed on purpose" claim becomes false the moment this lands
(`H7c-SCOPING.md` § 9 names it):

```python
"""One parameter's type, default, constraints and help text.

The constraint vocabulary is closed on purpose: docs/reference.md § Templates.

`requires_env` is the one keyword here that is **not** a constraint and is
deliberately absent from that closed table: it constrains the *environment* a
value may be used in, not the value. § A credential can belong to a parameter
value states the boundary and the reason — the provider is something you decide,
so it is a `Param`, and what that decision requires travels with it.
"""
```

Add the helper beneath `_TYPE_NAMES`:

```python
def _joined(values: list[Any]) -> str:
    return ", ".join(str(v) for v in values)
```

Add the argument to `__init__`'s signature, after `nullable` and before `help`:

```python
        nullable: bool = False,
        requires_env: dict[Any, list[str]] | None = None,
        help: str | None = None,
```

Add the checks after the existing `ge/gt/le/lt` guard and before the attribute assignments, so a
`requires_env` fault is raised alongside the other construction faults rather than after a partly
built object exists:

```python
        if requires_env is not None:
            if choices is None:
                raise ValueError("requires_env requires choices: a credential requirement is "
                                 "only checkable over a closed set of values")
            absent = [c for c in choices if c not in requires_env]
            extra = [k for k in requires_env if k not in choices]
            if absent or extra:
                detail = ""
                if absent:
                    detail += f"; no key for {_joined(absent)}"
                if extra:
                    detail += f"; keys naming no choice: {_joined(extra)}"
                raise ValueError(
                    "requires_env must be total over choices: "
                    f"choices are {_joined(choices)}; "
                    f"requires_env names {_joined(list(requires_env))}{detail}"
                )
```

Store it beside `nullable`:

```python
        self.nullable = nullable
        self.requires_env = requires_env
```

- [ ] **Step 4: Run and see it pass.** `uv run pytest tests/test_param.py -q`, then the whole suite:
      **1957 + 4 new tests passed, 2 xfailed.** `uv run mypy` must be clean — `dict[Any, list[str]]`
      matches how `choices: list[Any]` is already typed, so a non-`str` choice stays legal.

- [ ] **Step 5: End-to-end confirmation that a fault is `E-TEMPLATE-LOAD`.** Append to
      `tests/test_validate.py` — its module-level names are `base_config`, `write_config`,
      `write_config_nondet`, `write_config_broken`, `write_config_exits`, `_DELETE`, `codes`,
      `messages_by_code`, `_validate_with`, `_error_codes`, plus the `_*_EXPERIMENT` source
      constants. `_CRED_TOTALITY_TEMPLATE` is free:

```python
_CRED_TOTALITY_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    parameter_spec = {
        "llm.provider": Param(
            str,
            default="azure_openai",
            choices=["azure_openai", "openai", "ollama"],
            requires_env={"azure_openai": ["AZURE_OPENAI_API_KEY"]},
        )
    }
"""


def test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding(
    git_repo: Path, write_config
):
    """The route, probed end to end rather than reasoned from the phrasing:
    `Param.__init__` raises `ValueError`, `discover_local` catches it and
    interpolates `{exc!r}` into an `E-TEMPLATE-LOAD` message. No new identifier.

    `!r` is why the fragments below are quoted the way they are — the message
    carries `ValueError('...')`, not the bare text.
    """
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "cred_assay.py").write_text(_CRED_TOTALITY_TEMPLATE)

    found = messages_by_code(write_config({"experiment_type": "cred_assay", "parameters": {}}))
    assert "E-CRED-MISSING" not in found        # a load fault is not a credential finding
    assert "E-CRED-PARAM-MISSING" not in found
    message = found["E-TEMPLATE-LOAD"]
    assert "cred_assay.py" in message
    assert "ValueError(" in message             # the repr, per `{exc!r}`
    assert "no key for openai, ollama" in message
    assert "choices are azure_openai, openai, ollama" in message

    # THE CONTROL, and it is what makes the assertion above about the totality
    # check rather than about local discovery: the same template with a total
    # mapping loads, and `E-TEMPLATE-LOAD` disappears.
    (templates / "cred_assay.py").write_text(
        _CRED_TOTALITY_TEMPLATE.replace(
            'requires_env={"azure_openai": ["AZURE_OPENAI_API_KEY"]},',
            'requires_env={"azure_openai": ["AZURE_OPENAI_API_KEY"],\n'
            '                          "openai": ["OPENAI_API_KEY"],\n'
            '                          "ollama": []},',
        )
    )
    assert "E-TEMPLATE-LOAD" not in codes(
        write_config({"experiment_type": "cred_assay", "parameters": {}})
    )
```

Run it. It must pass with the implementation from step 3 already in place.

- [ ] **Step 6: Mutate — three, each with the test that must go red.**

  **(a) Delete the totality check.** Remove the `if absent or extra:` block from
  `param.py`. `test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets` must
  FAIL at its first `pytest.raises` (no exception raised), and
  `test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding` must FAIL on its
  `found["E-TEMPLATE-LOAD"]` lookup with a `KeyError`. **Checked against the test bodies:** both
  call `Param(...)` with a deliberately partial mapping and both observe the raise, so both
  discriminate.

  **(b) Drop the `extra` half.** Change `if absent or extra:` to `if absent:`. Only the
  **second** `pytest.raises` block in
  `test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets` goes red — the
  unknown-key fixture has `choices=["a","b"]` fully keyed plus `"zz"`, so `absent` is empty and
  nothing raises. The first block still passes. **This is the mutation that proves the two branches
  are separately pinned**, which the code-only mutation (a) does not.

  **(c) Drop the `choices` requirement.** Remove the `if choices is None:` raise. The second half of
  `test_requires_env_is_stored_and_needs_choices` must FAIL — `Param(str, default="a",
  requires_env={"a": ["A_KEY"]})` would construct, and `pytest.raises(ValueError, match="choices")`
  reports `DID NOT RAISE`. Note that this mutation would *also* make `absent`/`extra` compute
  against `None` and raise `TypeError`, which is why the guard is a raise and not a silent skip —
  check that the failure you see is `DID NOT RAISE`, not a `TypeError`; if it is a `TypeError` the
  guard order in step 3 was transcribed wrong.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green. **Never `git checkout --`.**

- [ ] **Step 7: Which deliverable no mutation reaches.** `self.requires_env` being *stored* is
      pinned only by `test_requires_env_is_stored_and_needs_choices`'s two reads, which is enough —
      dropping the assignment gives `AttributeError`. **`_joined`'s output order** is not
      independently pinned: it follows `choices`'s declared order and the fixtures happen to declare
      them sorted. Deliberate and left — the order is `choices`'s, not this function's, and a
      fixture that separated them would be pinning `list` iteration order. Say so in the task
      report rather than adding an assertion.

- [ ] **Step 8: Verify and commit.** All four commands. `feat: Param(requires_env=) — the
      constructor argument, total over choices` — and note in the message that **this is the H7b
      prerequisite**.

---

