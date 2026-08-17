## Task 11: `E-TEMPLATE-UNKNOWN`'s `plugin` hint

**Files:** Modify `src/publishable/templates/registry.py`, `src/publishable/validate.py`,
`src/publishable/generators/experiment.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `registry.unknown_template_message(name: str, known: Sequence[str]) -> str`, whose body
  is `f"names \`{name}\`, which no template — core's, an installed plugin's, or this project's own
  \`templates/\` — registers (known: {', '.join(known)})"`, and which has exactly two callers:
  `validate.validate_config` and `generators/experiment.generate_experiment`. **§ Errors carries one
  row per code covering every emit site**, and this code has two.
- Produces: `unknown_template_message(name, known, plugin=None)`; the hint rendered at the
  `validate` site, which is the one that holds a config; and the `generate` site passing `None`
  explicitly, since no config exists there yet.

**Row 211, and the exact thing it asks for.** The row is *"`experiment_type` names `llm_diagnostic`,
which no installed plugin registers — `plugin` says it should come from
`someuser/publishable-llm`."* `validate_config` reports the code and lists the known names but not
the `plugin` field's hint. The row's own justification for waiting was that the hint "is only useful
once an unresolvable `experiment_type` can name a template some *uninstalled* distribution
registers, which is the entry-point resolution H7 owns" — task 7 lands that, so the wait is over.

**The one wording, and why the change is one wording rather than two.**
`unknown_template_message` exists so `validate`'s finding and `generate_experiment`'s raise cannot
drift; the re-scoping confirmed it is still the single source. Change it there and both surfaces
move. **Do not add a second literal at either call site.**

- [ ] **Step 1: Write the failing test.** Append to `tests/test_validate.py`:

```python
def test_an_unresolved_template_name_names_the_plugin_the_config_points_at(write_config):
    """Row 211. The hint is the config's own `plugin` field, which is a readable
    note beside `uv.lock` rather than an install instruction — so the message
    says where the template was expected to come from and does not offer to
    fetch it.
    """
    found = messages_by_code(
        write_config({"experiment_type": "llm_diagnostic", "plugin": "someuser/publishable-llm"})
    )
    message = found["E-TEMPLATE-UNKNOWN"]
    assert "llm_diagnostic" in message
    assert "someuser/publishable-llm" in message
    assert "generic" in message  # the known list is still printed

    # THE CONTROL: with no `plugin` declared the message must not invent one, and
    # must not carry the hint's connective either — a fragment that appeared
    # under both declarations would pin nothing.
    plain = messages_by_code(write_config({"experiment_type": "llm_diagnostic"}))["E-TEMPLATE-UNKNOWN"]
    assert "someuser/publishable-llm" not in plain
    assert "`plugin` says" not in plain
```

- [ ] **Step 2: Run and see it fail.** The first `assert "someuser/publishable-llm" in message`
      fails; the control passes already, which is expected and proves nothing until its sibling does.

- [ ] **Step 3: Implement.** In `registry.py`:

```python
def unknown_template_message(
    name: str, known: Sequence[str], plugin: str | None = None
) -> str:
    """The one wording for a name neither `resolve_template` call site resolved —
    `validate`'s finding and `generate_experiment`'s raise both read this
    rather than each keeping its own copy, so the two surfaces cannot drift
    the way two hard-coded literals eventually would.

    Takes the already-resolved names rather than a repo root, so building the
    message costs no second discovery: each caller has just merged, and has
    them in hand.

    `plugin` is the config's own field, when the caller has a config. It is a
    readable note beside the authoritative pin in `uv.lock` rather than a second
    one — core never installs from it — so the hint says where the template was
    expected to come from and stops there. A caller with no config passes
    `None`: `generate experiment` is writing the file that would hold it.
    """
    hint = f" — `plugin` says it should come from `{plugin}`" if plugin else ""
    return (
        f"names `{name}`, which no template — core's, an installed plugin's, "
        f"or this project's own `templates/` — registers "
        f"(known: {', '.join(known)}){hint}"
    )
```

      In `validate.py`'s `validate_config`, the `E-TEMPLATE-UNKNOWN` branch task 9 wrote becomes:

```python
            plugin = doc.get("plugin")
            c.error(
                "E-TEMPLATE-UNKNOWN",
                "experiment_type",
                unknown_template_message(
                    name, known, plugin if isinstance(plugin, str) and plugin else None
                ),
            )
```

      The `isinstance` guard is not defensive padding: `plugin` is typed `str` by `LEAF_TYPES` and a
      wrong type there is `E-CONFIG-TYPE`'s finding, but a leaf fault is deliberately non-fatal, so
      this branch is reachable with a list or a mapping in that field and interpolating one would
      print a `repr` into a hint. The same reasoning `_check_units`' `input_dir` and `key` guards
      already carry.

      In `generators/experiment.py`, pass the third argument explicitly rather than relying on the
      default, so a reader of that call site sees the decision:

```python
        raise ContractError(
            unknown_template_message(template_name, known, plugin=None),
            code="E-TEMPLATE-UNKNOWN",
        )
```

- [ ] **Step 4: Update § Errors `validate` reports' `E-TEMPLATE-UNKNOWN` row.** It reads
      "`experiment_type` is missing, empty, or names a template neither core nor this project's own
      [`templates/`](#templates-where-parameters-are-defined) registers. An installed plugin's is
      not yet checked either: no entry point is resolved in this build, so there is no plugin
      registry for a name to be found in or missing from." **Delete the second sentence** and
      replace the first:

```
| `experiment_type` is missing, empty, or names a template that neither core, nor any installed distribution's `publishable.templates` entry points, nor this project's own [`templates/`](#templates-where-parameters-are-defined) registers — the installed set read from package metadata, so a name no distribution declares is refused without importing one. When the config declares a [`plugin`](#the-one-config-file), the message names it: that field is a readable note about where the template was expected to come from, so a reader who has not installed it learns that from the diagnostic rather than from a missing-name list. Two surfaces meet this condition — `validate` reports it as a finding, never raising it, and [`generate experiment`](#creation-commands) raises it as a `ContractError` — and this row governs both, the two built from one shared message; the hint appears only at the first, `generate` being the command that writes the file the field would live in | `E-TEMPLATE-UNKNOWN` |
```

- [ ] **Step 5: Strike Row 211.** Append to that section in `docs/superpowers/spec-defects.md`:

```markdown
**STRUCK 2026-08-16 (H7b Part A task 11).** `unknown_template_message` takes the config's `plugin`
field and renders it, so `validate`'s finding names where the template was expected to come from.
The row's stated precondition — that an unresolvable `experiment_type` can name a template some
uninstalled distribution registers — is satisfied by task 7's metadata scan and task 8's merge.
`generate experiment` passes `None` and shows no hint, deliberately: it is writing the file that
would hold the field.
```

- [ ] **Step 6: Run and see it pass**, then the whole suite. Every pre-existing
      `E-TEMPLATE-UNKNOWN` test must still pass **untouched** — none of them declares a `plugin`,
      so none sees the hint. Run `uv run pytest -q -k "unknown_template or TEMPLATE_UNKNOWN"` and
      read the list. Expected: predecessor's count **+ 1**.

- [ ] **Step 7: Mutate — two.**

  **(a) Render the hint unconditionally.** Change the `hint` line to
  `hint = f" — \`plugin\` says it should come from \`{plugin}\`"`.
  `test_an_unresolved_template_name_names_the_plugin_the_config_points_at` must FAIL on its control
  half: the second config declares `plugin: None`, so the mutant renders "`plugin` says it should
  come from `None`", and the test asserts "`plugin` says" is absent. **Checked against the body:**
  the control asserts on the *connective* rather than only on the value, which is what makes it
  discriminate — an assertion on `"someuser/publishable-llm" not in plain` alone would pass under
  this mutant.

  **(b) Interpolate the hint at the call site instead of in the shared message.** In `validate.py`,
  revert to `unknown_template_message(name, known)` and append the hint to the returned string.
  **This mutation cannot be caught by any test in the suite** — the rendered message is identical.
  Stated here rather than prescribed: the property at stake is that the two surfaces share one
  wording, and the only thing enforcing it is that `generate_experiment` has no hint to append.
  **Do not run this one**; it is recorded so nobody proposes it as proof of the shared-message
  property, which no test holds.

  Revert (a) by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 8: Which deliverable no mutation reaches.** **The `generate experiment` emit site is
      unpinned for the hint** — it passes `None` and no test asserts that it does, because the
      message it produces is byte-identical to the one it produced before this task. `tests/` does
      cover that site for the code itself; the *absence* of a hint there is not covered and nothing
      in this slice covers it. **The `isinstance` guard on `plugin`** is pinned by nothing either: no
      test declares a non-string `plugin`. Both stated; neither is closed later.

- [ ] **Step 9: Verify and commit.** All four commands.
      `feat: an unresolved experiment_type names the plugin the config points at`

---

