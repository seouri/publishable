## Task 11: The expansion modes the union must cover

**Files:** Modify `tests/test_validate.py`. Modify `src/publishable/validate.py` **only if a mode
turns out to be wrong** — this task's first job is to find out.

**Interfaces:**
- Consumes: `_check_requires_env` from task 10; `_UNION_TEMPLATE`, `_UNION_NAMES` and
  `_union_project` from task 10's additions to `tests/test_validate.py`;
  `sweep.NON_PRODUCT_MODES = ("baseline", "ablate")` and
  `sweep.removal_value(baseline: Mapping[str, Any], path: str) -> Any`, which returns `False` for a
  path the baseline fixes to a bool and `None` otherwise — read from `src/publishable/sweep.py`.
- Produces: no new interface. Four fixtures, one per mode the scoping's § 5 finding 3 names, plus
  the `ablate.remove` case the charter has no task for.

**Why these four and not the grid alone.** `NON_PRODUCT_MODES` means a `baseline` is a **resolved
condition**, not a description of one — so a baseline fixing `llm.provider` contributes its
credential to the union. `paired` couples two paths in one cell. `groups` contributes a **selector**
and therefore no parameter value at all, so a groups-only sweep's union is the base value's
requirement — a case that reads as a gap and is the correct answer. And `ablate.remove` against a
nullable parameter with `choices` resolves to `null`, which is a **legal resolved value with no key
in the mapping**: the union must skip it silently rather than treat it as an unknown key.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_validate.py`. Note the second
      template constant — `_UNION_TEMPLATE`'s `llm.provider` is not nullable, and `ablate.remove`
      needs a nullable target:

```python
_ABLATABLE_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    parameter_spec = {
        "llm.provider": Param(
            str,
            default="azure_openai",
            nullable=True,
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


def test_a_baseline_is_a_resolved_condition_whose_credential_joins_the_union(
    git_repo: Path, write_config, monkeypatch
):
    """`sweep.NON_PRODUCT_MODES` is `("baseline", "ablate")` — a baseline is not a
    description of a condition, it IS one, so the value it fixes is resolved and
    its credential is required. No fixture for this existed anywhere in the
    evidence base."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY",))
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {
                "baseline": {"llm.provider": "openai"},
                "grid": {"llm.retries": [1, 2]},
            },
        }
    )
    message = messages_by_code(path)["E-CRED-PARAM-MISSING"]
    assert "OPENAI_TEST_KEY" in message
    assert "OLLAMA_TEST_KEY" not in message


def test_a_paired_cell_resolves_both_of_its_paths(git_repo: Path, write_config, monkeypatch):
    """A `paired` entry couples two paths into one cell — the shape the
    feasibility analysis describes in prose for its Ollama case and shows in no
    YAML (`sweep.paired` is `[]` in both configs that have the key)."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY",))
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {
                "paired": [
                    {"llm.provider": "azure_openai", "llm.retries": 1},
                    {"llm.provider": "ollama", "llm.retries": 4},
                ]
            },
        }
    )
    message = messages_by_code(path)["E-CRED-PARAM-MISSING"]
    assert "OLLAMA_TEST_KEY" in message
    # Azure's key IS set, so the union reports one variable and not two — the
    # positive companion that keeps this from being an absence-only control.
    assert "AZURE_TEST_KEY" not in message


def test_a_groups_axis_contributes_no_parameter_value(
    git_repo: Path, tmp_path: Path, write_config, monkeypatch
):
    """A group level is a *set of units*, so it names no parameter and the union
    over a groups-only sweep is the base value's requirement — which is the
    correct answer rather than a gap.

    The roster is rewritten first: the `write_config` fixture writes
    `patient_id\\np1\\n` and nothing else, so `attributes: ["cohort"]` over that
    file earns `E-UNITS-ATTR-MISSING` and this test would pass for the wrong
    reason. `tmp_path / "input" / "index.csv"` is the file that fixture writes.
    """
    _union_project(git_repo, monkeypatch, set_names=())
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,cohort\np1,derivation\np2,derivation\np3,validation\np4,validation\n"
    )
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {"groups": {"cohort": ["derivation", "validation"]}},
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["cohort"],
            },
        }
    )
    found = [
        f for f in _findings_of(path) if f.code == "E-CRED-PARAM-MISSING"
    ]
    assert len(found) == 1, [f.message for f in found]
    assert "AZURE_TEST_KEY" in found[0].message   # the base value's, in both cells
    assert "OPENAI_TEST_KEY" not in found[0].message


def test_ablate_remove_resolves_a_value_with_no_key_and_requires_nothing(
    git_repo: Path, write_config, monkeypatch
):
    """`sweep.removal_value` sets a nullable parameter to `null`. `requires_env` is
    total over `choices`, and `null` is not a choice — so the ablated condition
    requires nothing, silently. Reporting it would be a second report of a fault
    `_check_sweep` owns.

    The control is on the same document: the BASELINE condition still resolves
    `openai` and still reports, so this test cannot pass by the check never
    running.
    """
    for name in _UNION_NAMES:
        monkeypatch.delenv(name, raising=False)
    templates = git_repo / "templates"
    templates.mkdir(exist_ok=True)
    (templates / "cred_assay.py").write_text(_ABLATABLE_TEMPLATE)
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {
                "baseline": {"llm.provider": "openai"},
                "ablate": [{"remove": ["llm.provider"]}],
            },
        }
    )
    found = [f for f in _findings_of(path) if f.code == "E-CRED-PARAM-MISSING"]
    assert len(found) == 1, [f.message for f in found]
    assert "OPENAI_TEST_KEY" in found[0].message   # the baseline's, and only it
```

and one helper — **`_findings_of` is a new name; `tests/test_validate.py`'s module level already
holds `base_config`, `write_config`, `write_config_nondet`, `write_config_broken`,
`write_config_exits`, `_DELETE`, `codes`, `messages_by_code`, `_validate_with`, `_error_codes` and
the `_*_TEMPLATE`/`_*_EXPERIMENT` constants, none of which is `_findings_of`**:

```python
def _findings_of(path: Path) -> list:
    """Every finding, not just its code or its message — the shape a test needs
    when it must count findings of one code rather than test membership."""
    c = Collector()
    validate_config(path, c)
    return list(c.findings)
```

- [ ] **Step 2: Run each test and record what it does.** **Expect some of these to pass
      immediately** — task 10's implementation is written to handle all four — and treat that as the
      measurement this task exists to take, not as a reason to skip it. For any that **fails**,
      diagnose before changing anything: `sweep.expand`'s output for that document is the ground
      truth. Run
      `uv run python -c "from publishable.sweep import expand; import yaml; print(expand(yaml.safe_load(open('<path>').read())))"`
      and read the `Condition` list. Only then change `validate.py`, and record the change in the
      task report as a real disagreement found.

- [ ] **Step 3: Check each config actually validates for the reason you think.** Every one of these
      documents can earn unrelated findings — a `groups` axis needs `data.units.attributes`, an
      `ablate` needs a `baseline`, a `paired` entry's values must be nameable. **Print
      `codes(path)` for each fixture once and read the whole set** before believing any assertion
      about `E-CRED-PARAM-MISSING`. `CLAUDE.md`: a refusal that happens to fire must be
      attributed before it is counted. If a fixture earns an unrelated error, fix the fixture — do
      not weaken the assertion.

- [ ] **Step 4: Mutate — one, chosen because the obvious one is blind.**

  **The obvious mutation is deleting the `if path in condition.selectors: continue` guard, and it
  cannot discriminate** — `wanted` is keyed on `parameter_spec` paths and a group axis's name is
  not one, so the mutant behaves identically on every fixture above. Do not use it. (Task 10 step 7
  prescribes the one experiment that could change this answer; if it succeeded, use that fixture
  here instead and say so.)

  **Use instead: resolve only the first condition.** Change `for condition in conditions:` to
  `for condition in conditions[:1]:`. **`test_a_baseline_is_a_resolved_condition_whose_credential_joins_the_union`
  must FAIL**? Check first: `expand` emits the baseline's rows **first**, so a baseline fixture's
  requiring condition *is* condition 0 and this mutation would be blind on it.
  **`test_a_paired_cell_resolves_both_of_its_paths` is the one that must FAIL** — its two `paired`
  entries are conditions 0 and 1, and the requiring one (`ollama`) is **second**, so truncating to
  the first leaves `OLLAMA_TEST_KEY` unreported and the `messages_by_code(path)[...]` lookup raises
  `KeyError`. **Name that test in the brief and verify the ordering by printing
  `[c.values for c in expand(doc)]` before trusting it.**

  A second, on the same principle: **replace `first_seen.setdefault` with `first_seen[…] = …`**.
  `test_a_variable_two_conditions_need_is_reported_once` (task 10's) must still pass — it counts
  findings, not attributions — but the *attribution* changes, so add the assertion that pins it if
  it is not already pinned: in the paired fixture, assert the message names `` `ollama` `` rather
  than a later condition's value. If no fixture can distinguish first-wins from last-wins, **say so
  and drop this second mutation** rather than defending it.

  Revert by editing back; delete `__pycache__`; re-run.

- [ ] **Step 5: Which deliverable no mutation reaches.** The **`ablate.remove` silence** is proved
      by a test whose positive companion is the baseline's own finding on the same document, so it
      is not an absence-only control — but **no mutation makes it go red**, because the behaviour is
      "does nothing" and every plausible mutant that reports would break the count assertion, which
      is the mutation. State it as covered-by-count rather than covered-by-mutation, and if
      `.get(value)` on an absent key ever stops returning `None`, the count assertion is what
      catches it.

- [ ] **Step 6: Verify and commit.** All four commands.
      `test: the union over baseline, paired, groups, and ablate.remove`

---

