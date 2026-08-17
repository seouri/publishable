## Task 4: `Param.comment()` renders the requirement against every choice

**Files:** Modify `src/publishable/param.py`, `tests/test_param.py`.

**Interfaces:**
- Consumes: `Param.comment(self) -> str`, and `self.requires_env` from task 3.
- Produces: a `choices` comment carrying each value's variables, exactly as `reference.md`
  § A credential can belong to a parameter value renders it:
  `choices: azure_openai (needs AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama`.

**Against every choice, not the written one**, because nothing ever writes back into a config and a
comment describing the *current* value would be wrong the first time the file was edited. That is
the property every other inline comment already has.

**The blast radius, measured.** `grep -rn "choices:" tests/ docs/reference.md src/publishable/` at
`478c1f3` returns six sites: `tests/test_param.py` (the `comment()` unit assertion),
`tests/test_materialize.py` (`# choices: pearson | spearman | kendall` in a generated config),
`reference.md`'s worked-example config line, its § Templates constraint table row, its
§ A credential can belong to a parameter value example, and its § Secrets-adjacent parameter table.
**`generic` declares no `requires_env`, so both test sites must be byte-identical after this task** —
that is the regression control, and it already exists.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_param.py`:

```python
def test_a_choices_comment_carries_each_value_s_credential_against_every_choice():
    """`reference.md` § A credential can belong to a parameter value shows this
    exact string. Every choice is annotated, not the default — a comment about
    the current value would be wrong the first time the config was edited.

    Three choices, not two, and the annotated ones are NOT contiguous with the
    default: with two, "annotate every choice" and "annotate the written one"
    both produce a one-annotation string for some arrangement.
    """
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
    assert p.comment() == (
        "choices: azure_openai (needs AZURE_OPENAI_API_KEY) | "
        "openai (needs OPENAI_API_KEY) | ollama"
    )


def test_a_value_needing_two_variables_names_both_in_its_own_parenthesis():
    p = Param(
        str,
        default="a",
        choices=["a", "b"],
        requires_env={"a": ["A_ONE", "A_TWO"], "b": []},
    )
    assert p.comment() == "choices: a (needs A_ONE, A_TWO) | b"
```

And leave `test_comments_render_the_constraint_that_claims_them` **untouched** — its
`Param(str, default="a", choices=["a", "b"]).comment() == "choices: a | b"` is the regression
control for a parameter with no `requires_env`, and it must still pass unchanged.

- [ ] **Step 2: Run and see it fail.** Both new tests fail on the missing `(needs …)` suffix.

- [ ] **Step 3: Implement.** In `param.py`, replace `comment()`'s first branch and add one helper
      method beneath `comment()`:

```python
    def comment(self) -> str:
        """The inline comment `init` renders. One constraint claims it, else `help`.

        A `choices` comment additionally carries each value's `requires_env`
        variables. Those are not a constraint — see this module's docstring —
        and they are rendered against *every* choice rather than the written
        one, because nothing ever writes back into a config and a comment about
        the current value would be wrong the first time the file was edited.
        """
        if self.choices is not None:
            return "choices: " + " | ".join(self._choice_label(c) for c in self.choices)
```

(the rest of the body is unchanged), and:

```python
    def _choice_label(self, choice: Any) -> str:
        needs = (self.requires_env or {}).get(choice) or []
        if not needs:
            return str(choice)
        return f"{choice} (needs {', '.join(needs)})"
```

- [ ] **Step 4: Run and see it pass.** `uv run pytest tests/test_param.py tests/test_materialize.py -q`
      first — `test_materialize.py`'s `# choices: pearson | spearman | kendall` is the generated-file
      regression and must be untouched — then the whole suite.

- [ ] **Step 5: Mutate — two.**

  **(a) Render the written value's annotation everywhere.** Change the join to
  `self._choice_label(self.default) for c in self.choices`.
  `test_a_choices_comment_carries_each_value_s_credential_against_every_choice` must FAIL: it would
  produce `choices: azure_openai (needs AZURE_OPENAI_API_KEY) | azure_openai (needs
  AZURE_OPENAI_API_KEY) | azure_openai (needs AZURE_OPENAI_API_KEY)`. **Checked against the test
  body:** the assertion is an exact string equality over a three-choice fixture whose annotations
  differ, so it discriminates. Note that `test_comments_render_the_constraint_that_claims_them` also
  goes red under this mutation (`choices: a | a`), which is fine — the mutation must fail *at least*
  the named test.

  **(b) Drop the empty-list distinction.** Change `if not needs:` to `if needs is None:`. Then
  `ollama`, whose value is `[]`, renders as `ollama (needs )`. The first new test must FAIL.
  **This is the mutation that pins `[]` as "needs nothing" rather than as a missing key**, which
  mutation (a) does not reach.

  Revert each by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 6: Which deliverable no mutation reaches.** The **generated config's** rendering — the
      path from `comment()` through `materialize.py` into a real `config.yaml` — is exercised only
      for `generic`, which declares no `requires_env`, so `tests/test_materialize.py` proves the
      *absence* case and nothing proves the presence case end to end at this commit. That is
      accepted here: no template in the tree declares `requires_env`, and inventing a local one
      purely to render a comment would test `materialize.py`'s existing loop rather than this task.
      **Task 10's fixture is the first local template that declares one**; if its config is
      generated rather than hand-written it closes this incidentally — do not force it.

- [ ] **Step 7: Verify and commit.** All four commands.
      `feat: a choices comment carries each value's requires_env, against every choice`

---

