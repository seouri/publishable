## Task 10: The `requires_env` union over the conditions the sweep resolves

**Files:** Modify `src/publishable/validate.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `expand(config: dict[str, Any]) -> list[Condition]` from `publishable.sweep`, already
  imported in `validate.py`; `Condition(index: int, label: str | None, values: Mapping[str, Any],
  is_baseline: bool, selectors: frozenset[str])` — read from `src/publishable/sweep.py`;
  `_flatten(node: Any, prefix: str = "") -> dict[str, Any]` and `MISSING`, both already in
  `validate.py`; `Param.requires_env` from task 3; `missing_env` from task 7.
- Produces: `_check_requires_env(doc: dict[str, Any], template: Any, c: Collector) -> None`,
  emitting `E-CRED-PARAM-MISSING`.

**How a condition's value is resolved, and why not through `runner.resolve_condition_cfg`.**
`resolve_condition_cfg` deep-copies the whole document and returns a `Config`; this check needs one
dotted path's value, for each of a handful of paths, once per condition. The overlay is the same
three lines it performs — declared parameters, then each of `condition.values` whose path is **not**
in `condition.selectors` — computed locally against `_flatten`, which `_check_parameters` already
uses for exactly this. `validate.py` does not import `runner` today and this task does not make it.
**The selector skip is `resolve_condition_cfg`'s own rule and its reason is quoted at that function:
a group cell names no parameter at all**, so laying `{arm: control}` over `parameters` would invent
an `arm` no `parameter_spec` declares.

**Decision 6's fixture, sized by counting the readings first.** There are **three** candidate
readings of "what does this config require", and two choices cannot separate them:

| Reading | What it answers on the fixture below |
|---|---|
| **A — the union over the conditions the sweep resolves** (the specified one) | `OPENAI_API_KEY` alone |
| **B — the union over all `choices`** | `OPENAI_API_KEY` **and** `OLLAMA_HOST_KEY` |
| **C — the requirement of the value written in `parameters`** | nothing |

The fixture: three choices; `requires_env` giving a **non-empty** requirement to all three;
`sweep.grid` selecting two of them; the Azure key **set**, the OpenAI key **unset**, and the third
choice's key **unset and never selected**. Note the deviation from `reference.md`'s own example,
which gives `ollama` an empty `[]`: copying that collapses A and B, because an unselected choice
requiring nothing produces the same answer either way. **The third choice must require something.**

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_validate.py`:

```python
_UNION_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    parameter_spec = {
        "llm.provider": Param(
            str,
            default="azure_openai",
            choices=["azure_openai", "openai", "ollama"],
            requires_env={
                "azure_openai": ["AZURE_TEST_KEY"],
                "openai": ["OPENAI_TEST_KEY"],
                "ollama": ["OLLAMA_TEST_KEY"],
            },
        ),
        "llm.retries": Param(int, default=2, ge=0),
    }
"""

_UNION_NAMES = ("AZURE_TEST_KEY", "OPENAI_TEST_KEY", "OLLAMA_TEST_KEY")


def _union_project(git_repo: Path, monkeypatch, *, set_names: tuple[str, ...]) -> None:
    """The decision-6 fixture: three choices, a sweep selecting two, a third whose
    variable is deliberately unset and whose requirement is deliberately NON-empty.

    `reference.md`'s own example gives `ollama` an empty `[]`; copying it here
    would collapse "union over resolved conditions" into "union over all
    choices", since an unselected choice requiring nothing answers the same
    either way.

    Every one of the three names is `delenv`-ed first and only `set_names` is
    exported, so the answer is a property of the check rather than of the machine
    the suite runs on.
    """
    for name in _UNION_NAMES:
        monkeypatch.delenv(name, raising=False)
    for name in set_names:
        monkeypatch.setenv(name, "value")
    templates = git_repo / "templates"
    templates.mkdir(exist_ok=True)
    (templates / "cred_assay.py").write_text(_UNION_TEMPLATE)


def test_the_union_is_over_the_conditions_the_sweep_resolves(
    git_repo: Path, write_config, monkeypatch
):
    """Reading A. B would additionally report `OLLAMA_TEST_KEY`; C would report
    nothing, `azure_openai` being the written value and its key set."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY",))
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {"grid": {"llm.provider": ["azure_openai", "openai"]}},
        }
    )

    c = Collector()
    validate_config(path, c)
    found = [f for f in c.findings if f.code == "E-CRED-PARAM-MISSING"]

    assert len(found) == 1, [f.message for f in found]
    message = found[0].message
    assert found[0].path == "parameters.llm.provider"
    assert "OPENAI_TEST_KEY" in message          # reading A's answer …
    assert "OLLAMA_TEST_KEY" not in message      # … and not reading B's
    # The three facts this code's message must name and the other one cannot:
    # the parameter (via `path` above), the value, and the condition.
    assert "`openai`" in message
    assert "condition `provider=openai`" in message


def test_the_union_says_nothing_when_every_selected_value_s_key_is_set(
    git_repo: Path, write_config, monkeypatch
):
    """The honouring. The unselected `ollama`'s key stays unset throughout — so a
    check that reported over all `choices` fails here while passing the test
    above."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY", "OPENAI_TEST_KEY"))
    assert codes(
        write_config(
            {
                "experiment_type": "cred_assay",
                "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
                "sweep": {"grid": {"llm.provider": ["azure_openai", "openai"]}},
            }
        )
    ) == set()


def test_an_undeclared_parameter_falls_back_to_the_template_s_default(
    git_repo: Path, write_config, monkeypatch
):
    """A config that omits the parameter still resolves to a value — the
    template's default — and that value's credential is still required."""
    _union_project(git_repo, monkeypatch, set_names=())
    path = write_config({"experiment_type": "cred_assay", "parameters": {}})
    message = messages_by_code(path)["E-CRED-PARAM-MISSING"]
    assert "AZURE_TEST_KEY" in message
    assert "the base parameters" in message      # no sweep, so no condition label


def test_a_variable_two_conditions_need_is_reported_once(
    git_repo: Path, write_config, monkeypatch
):
    """One missing value is one thing to fix. Attributed to the first condition
    that selected it, which is why the assertion below names `openai` and not the
    later duplicate."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY",))
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {
                "grid": {
                    "llm.provider": ["openai", "azure_openai"],
                    "llm.retries": [1, 2],
                }
            },
        }
    )
    c = Collector()
    validate_config(path, c)
    found = [f for f in c.findings if f.code == "E-CRED-PARAM-MISSING"]
    assert len(found) == 1, [f.message for f in found]
    assert "OPENAI_TEST_KEY" in found[0].message


def test_a_template_declaring_no_requires_env_reports_nothing(write_config, monkeypatch):
    """`generic`'s four parameters declare none, which is why the other 1957 tests
    are unaffected. Asserted rather than assumed."""
    for name in _UNION_NAMES:
        monkeypatch.delenv(name, raising=False)
    assert "E-CRED-PARAM-MISSING" not in codes(write_config())
```

- [ ] **Step 2: Run and see them fail.** The three reporting tests fail on an empty `found`
      / `KeyError`; the two clean ones pass already.

- [ ] **Step 3: Implement.** In `validate.py`:

```python
def _check_requires_env(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """The union over the conditions the sweep actually resolves.

    That union is the entire reason a value carries its own credential
    requirement instead of a template carrying a static list: a config selecting
    Azure and OpenAI must say nothing about Ollama's key, and one selecting none
    of them must say nothing about any. `reference.md` § A credential can belong
    to a parameter value.

    A condition's value is resolved the way `runner.resolve_condition_cfg`
    resolves it — declared parameters, then each of `condition.values` whose path
    is not a **selector**, a group cell naming no parameter at all — computed
    locally rather than by importing the runner, since this needs one path's
    value rather than a whole `Config`.

    A resolved value with no key in the mapping requires nothing. `requires_env`
    is total over `choices`, so that case is exactly the values `choices` does
    not hold: `sweep.ablate.remove` sets a nullable parameter to `null`, which is
    a legal resolved value and not a choice. Reporting it here would be a second
    report of a fault `_check_sweep` already owns.

    One finding per variable, attributed to the first condition that selected it:
    one missing value is one thing to fix, whatever selected it.
    """
    spec = getattr(template, "parameter_spec", None) or {}
    wanted = {path: p for path, p in spec.items() if getattr(p, "requires_env", None)}
    if not wanted:
        return
    try:
        conditions = expand(doc)
    except Exception:
        # Guarded the same way `_condition_labels` guards its own `expand(doc)`:
        # an unexpandable sweep is `_check_sweep`'s to report, and this module
        # collects rather than raises.
        return
    declared = _flatten(doc.get("parameters"), "")
    # `dict`, so insertion order is condition order then declared-parameter
    # order — a deterministic finding order without sorting away the attribution.
    first_seen: dict[str, tuple[str, Any, str | None]] = {}
    for condition in conditions:
        resolved = dict(declared)
        for path, value in condition.values.items():
            if path in condition.selectors:
                continue
            resolved[path] = value
        for path, param in wanted.items():
            if path in resolved:
                value = resolved[path]
            elif param.default is not MISSING:
                value = param.default
            else:
                continue  # required and absent — `E-PARAM-MISSING`'s finding, not this one
            try:
                needs = param.requires_env.get(value)
            except TypeError:
                continue  # an unhashable resolved value cannot key the mapping
            for variable in needs or []:
                first_seen.setdefault(variable, (path, value, condition.label))
    for variable in missing_env(first_seen):
        path, value, label = first_seen[variable]
        where = f"condition `{label}`" if label else "the base parameters"
        c.error(
            "E-CRED-PARAM-MISSING",
            f"parameters.{path}",
            f"is `{value}` in {where}, which requires `{variable}` — no value in the "
            "environment or in `.env`",
        )
```

Call it from `validate_config`, immediately after `_check_required_env(doc, template, c)`.

- [ ] **Step 4: Run and see them pass.** New tests, then the full suite.

- [ ] **Step 5: Confirm the condition label the message prints.** The assertion
      `"condition \`provider=openai\`"` is **derived, not assumed**: run
      `uv run python -c "from publishable.sweep import expand; print([c.label for c in expand({'sweep': {'grid': {'llm.provider': ['azure_openai','openai']}}})])"`
      and write the literal it prints into the test. If `sweep.label_for` renders it differently,
      **the printed value wins** — `CLAUDE.md`: derive expected values from the fixture, never from
      an assumption about it.

- [ ] **Step 6: Mutate — three.**

  **(a) Union over all `choices` instead of resolved conditions.** Replace the per-condition loop
  body's value resolution with `for value in param.requires_env:` (iterating the mapping's keys).
  `test_the_union_is_over_the_conditions_the_sweep_resolves` must FAIL on
  `"OLLAMA_TEST_KEY" not in message` — actually on `len(found) == 1`, which becomes 2.
  **Checked against the test body:** the fixture gives `ollama` a non-empty requirement and leaves
  its key unset, so readings A and B genuinely differ. **This is the mutation decision 6 sizes the
  fixture for**, and with `reference.md`'s two-annotated-choices example it would have been blind.

  **(b) Only the written value.** Delete the per-condition overlay so `resolved` is `declared`
  alone. `test_the_union_is_over_the_conditions_the_sweep_resolves` must FAIL — reading C reports
  nothing, and `len(found) == 1` becomes 0.

  **(c) Drop the default fallback.** Change `elif param.default is not MISSING:` to
  `else: continue`. `test_an_undeclared_parameter_falls_back_to_the_template_s_default` must FAIL
  with `KeyError: 'E-CRED-PARAM-MISSING'`.

  Revert each by editing back; delete `__pycache__`; re-run.

- [ ] **Step 7: Which deliverable no mutation reaches, and one honest attempt.** The
      **`condition.selectors` skip** is not reachable by any mutation the fixtures above support:
      `wanted` is keyed on `parameter_spec` paths, and a group axis's path names no parameter, so
      deleting the skip changes nothing observable. **Attempt one fixture before accepting this** —
      a `sweep.groups` axis named exactly `llm.provider`, i.e.
      `{"sweep": {"groups": {"llm.provider": ["ollama"]}}}` — and see whether `validate` accepts the
      config. If it does, the skip is pinned (without it the union would read `ollama`'s
      requirement; with it, the base value's) and the fixture belongs in **task 11**, which owns
      the `groups` mode. **If `validate` refuses the config for an unrelated reason, record the
      code it refused with and accept the skip as unpinned**, on the grounds that it mirrors
      `resolve_condition_cfg`'s own documented rule rather than inventing one. Say which of the two
      happened in the task report; do not leave it undetermined.

  Also unpinned: the `except TypeError` guard around `.get(value)`. No fixture here declares a
  `list`-typed parameter with `requires_env`, and `Param` does not forbid it. Named and left.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: the requires_env union over the conditions the sweep resolves`

---

