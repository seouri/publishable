## Task 18: `--plugin` built — `uv add`, and the `plugin` field written

**Files:** Modify `src/publishable/cli.py`, `src/publishable/generators/experiment.py`,
`src/publishable/materialize.py`, `docs/reference.md`, `tests/test_cli.py`,
`tests/test_materialize.py`.

**Interfaces:**
- Consumes: `cli._dispatch_generate(command, rest) -> int`, which parses `--x y` pairs into `opts`
  and everything else into `positional`, then checks
  `missing = [f"--{o}" for o in ("template", "input-dir", "output-dir") if o not in opts]`;
  `generators.experiment.generate_experiment(*, repo_root, name, template_name, input_dir,
  output_dir) -> Path`; `materialize.materialize_config(*, template, template_name, name, input_dir,
  output_dir, entrypoint) -> str`, which writes the literal `"plugin: null"`;
  `subprocess.run`, used by `scaffold.py` for `git init`/`git add`/`git commit` and the pattern to
  follow.
- Produces: `generate_experiment(..., plugin: str | None = None)`; `materialize_config(...,
  plugin: str | None = None)` writing `plugin: <value>` or `plugin: null`; a `uv add
  git+https://github.com/<user>/<repo>` run before the package is scaffolded; the three `NOT BUILT`
  markings task 6 added, reverted.

**Order matters and the reason is the same one `generate template` already carries.** `uv add` must
run **before** anything reaches disk, and before `resolve_template`: the whole point of `--plugin`
is that the template it names comes from the package being installed, so resolving first would
refuse a name the install is about to provide. And a failed install must leave no half-scaffolded
package — `generate experiment` already refuses if `src/<pkg>/` exists, so a retry after a failed
install must find a clean tree.

**`--plugin` is legal on a creation command**, which task 6 wrote into § Plugins. Do not re-argue it
here.

**The install is real, so the test is marked.** `pyproject.toml` declares
`markers = ["slow: exercises real uv or network"]`. A test that actually runs `uv add
git+https://…` needs the network and is `@pytest.mark.slow`; the ordinary tests patch the runner.
**Patch by full module attribute path** — `publishable.generators.experiment.<name>` — and say so in
the test's own comment, since the same helper name could plausibly live in `cli`.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_materialize.py`:

```python
def test_the_plugin_field_carries_what_generate_was_told(tmp_path: Path):
    """`plugin` is a readable note beside the authoritative pin in `uv.lock`
    rather than a second one — so it records the argument verbatim, including a
    version suffix, and core never installs from the field itself."""
    text = materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir=str(tmp_path / "in"),
        output_dir=str(tmp_path / "out"),
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
        plugin="someuser/publishable-llm@v1.2.0",
    )
    assert yaml.safe_load(text)["plugin"] == "someuser/publishable-llm@v1.2.0"

    # THE CONTROL, and the regression: with no plugin the field is `null`, which
    # is what every other test in this file's generated config asserts.
    plain = materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir=str(tmp_path / "in"),
        output_dir=str(tmp_path / "out"),
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
    )
    assert yaml.safe_load(plain)["plugin"] is None
```

      and to `tests/test_cli.py`. **The invocation pattern is this file's own and is not invented
      here**: `main(["new", str(root)])` scaffolds, `monkeypatch.chdir(root)` puts
      `_dispatch_generate`'s `find_repo_root(Path.cwd())` in the right place, and `main([...])` is
      compared against `EXIT_OK` / `EXIT_WRONG` — read
      `test_generate_experiment_cli_resolves_a_project_local_template` and follow it exactly.
      `main`, `EXIT_OK` and `EXIT_WRONG` are already imported at module level, as are `yaml`,
      `pytest` and `Path`. **Add no module-level helper**; the file's existing ones are
      `run_a_project`, `_new_project_with_a_generated_template` and `GENERATED_TEMPLATE`, and
      nothing here needs a fourth.

```python
def test_generate_experiment_installs_the_plugin_before_it_scaffolds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The order is the behaviour: `uv add` runs before `resolve_template`,
    because the template the config names is the one being installed.

    Patched at `publishable.generators.experiment.uv_add` — the full module
    attribute path, since a same-named helper in `cli` would be a plausible
    wrong target.
    """
    calls: list[tuple[str, str]] = []

    def fake_uv_add(repo_root: Path, requirement: str) -> None:
        calls.append((str(repo_root), requirement))

    monkeypatch.setattr("publishable.generators.experiment.uv_add", fake_uv_add)

    root = tmp_path / "proj"
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\n")
    assert main(["new", str(root)]) == EXIT_OK
    monkeypatch.chdir(root)

    assert (
        main(
            [
                "generate",
                "experiment",
                "pilot",
                "--template",
                "generic",
                "--plugin",
                "someuser/publishable-llm",
                "--input-dir",
                str(data),
                "--output-dir",
                str(tmp_path / "results"),
            ]
        )
        == EXIT_OK
    )
    assert calls == [(str(root), "git+https://github.com/someuser/publishable-llm")]
    config = yaml.safe_load((root / "configs" / "pilot" / "config.yaml").read_text())
    assert config["plugin"] == "someuser/publishable-llm"

    # THE CONTROL: no `--plugin`, no install, and the field stays `null`. Without
    # it, an implementation that always installed would pass the assertion above.
    calls.clear()
    assert (
        main(
            [
                "generate",
                "experiment",
                "pilot2",
                "--template",
                "generic",
                "--input-dir",
                str(data),
                "--output-dir",
                str(tmp_path / "results2"),
            ]
        )
        == EXIT_OK
    )
    assert calls == []
    plain = yaml.safe_load((root / "configs" / "pilot2" / "config.yaml").read_text())
    assert plain["plugin"] is None


def test_a_failed_plugin_install_scaffolds_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """A retry after a failed install must find a clean tree — `generate
    experiment` refuses an existing `src/<pkg>/`, so a half-scaffolded package
    would make the failure permanent."""

    def fake_uv_add(repo_root: Path, requirement: str) -> None:
        raise ContractError("uv add failed: no such repository", code="E-UV-ADD")

    monkeypatch.setattr("publishable.generators.experiment.uv_add", fake_uv_add)

    root = tmp_path / "proj"
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\n")
    assert main(["new", str(root)]) == EXIT_OK
    monkeypatch.chdir(root)

    assert (
        main(
            [
                "generate",
                "experiment",
                "pilot",
                "--template",
                "generic",
                "--plugin",
                "someuser/publishable-llm",
                "--input-dir",
                str(data),
                "--output-dir",
                str(tmp_path / "results"),
            ]
        )
        == EXIT_WRONG
    )
    assert "E-UV-ADD" in capsys.readouterr().err
    assert not (root / "src" / "pilot").exists()
    assert not (root / "configs" / "pilot").exists()
```

      **`EXIT_WRONG` is asserted rather than "not `EXIT_OK`"** because this file's own control
      pattern does that — `test_generate_experiment_cli_resolves_a_project_local_template` asserts
      the specific exit code *and* the specific identifier on stderr, "not just some refusal". If a
      `ContractError` from `generate_experiment` reaches `main`'s handler as some other exit code,
      **read `main`'s dispatch and assert what it actually produces** rather than weakening the
      assertion; record what you found in the task report.

- [ ] **Step 2: Run and see them fail.** The materialize test on
      `TypeError: materialize_config() got an unexpected keyword argument 'plugin'`; the CLI tests
      on `AttributeError` from the `monkeypatch.setattr` target, which does not exist yet.

- [ ] **Step 3: Implement.** In `src/publishable/materialize.py`, add `plugin: str | None = None` to
      `materialize_config`'s keyword-only parameters and replace the literal `"plugin: null"` with:

```python
        f"plugin: {plugin if plugin else 'null'}",
```

      In `src/publishable/generators/experiment.py`, add `import subprocess` and:

```python
def uv_add(repo_root: Path, requirement: str) -> None:
    """`uv add <requirement>` in the project, and nothing more.

    `reference.md` § Plugins: no registry, no bespoke installer, no new trust
    boundary beyond "this is a git dependency," because it is one. The install
    is what makes the plugin a normal `pyproject.toml` line and a pinned
    `uv.lock` entry, which is what gives `reproduce` the exact version free.
    """
    result = subprocess.run(
        ["uv", "add", requirement], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise ContractError(
            f"`uv add {requirement}` failed: {result.stderr.strip() or result.stdout.strip()}",
            code="E-UV-ADD",
        )


def plugin_requirement(spec: str) -> str:
    """`<user>/<repo>` or `<user>/<repo>@<ref>` to what `uv add` takes."""
    return f"git+https://github.com/{spec}"
```

      and give `generate_experiment` a `plugin: str | None = None` keyword, installing **first**:

```python
    if plugin:
        uv_add(repo_root, plugin_requirement(plugin))
    template, known = resolve_template(template_name, repo_root)
```

      passing `plugin=plugin` through to `materialize_config`. In `cli._dispatch_generate`'s
      `experiment` branch, pass `plugin=opts.get("plugin")`. **`--plugin` must not join the
      `missing` list** — it is optional; read that list and confirm you did not add it.

      **Add `E-UV-ADD` to § Errors core raises**, beside the row that reports a project-local
      `templates/*.py` failing to load — name that sibling by what it does:

```
| `uv add` failing for a [`--plugin`](#plugins-where-domain-knowledge-lives) argument on `generate experiment`. Raised before anything reaches disk, so a retry finds a clean tree: `generate experiment` refuses an existing `src/<pkg>/`, which would make a half-scaffolded failure permanent. The message carries `uv`'s own output, since what went wrong is `uv`'s to say — a bad repository name, a ref that does not exist, no network | `ContractError` · `E-UV-ADD` |
```

- [ ] **Step 4: Revert task 6's three markings.** § Creation commands' `generate` row loses
      `(NOT BUILT — the flag parses and is dropped)`; § Generators' `experiment` row loses the
      sentence task 6 appended; § Plugins' opening sentence loses `— **NOT BUILT** in this build,
      where the flag parses and is dropped`. **Leave task 6's step-5 paragraph** about creation
      versus operation commands — it is a permanent clarification, not a marking. Re-read § Plugins
      after editing and confirm the paragraph still reads as one sentence's worth of correction
      rather than two.

- [ ] **Step 5: Config completeness.** § The one config file's fenced example already carries
      `plugin: null`; nothing is added by this task, and the identifying-fields paragraph already
      says "`plugin` names where the template came from, and is a readable note beside the
      authoritative pin in `uv.lock` rather than a second one — core never installs from it". Read
      that clause and confirm it is still true: **core installs from the flag, never from the
      field**, which is exactly what it says. Change nothing.

- [ ] **Step 6: A slow test that runs the real thing.** Add one, marked, so the patched tests are
      not the only evidence `uv add` is invoked correctly:

```python
@pytest.mark.slow
def test_uv_add_really_installs(tmp_path):
    """`markers = ["slow: exercises real uv or network"]`. The patched tests
    above prove the wiring; this proves the command line."""
```

      Fill it in against a real repository the project already depends on rather than inventing one,
      and if no such dependency is installable offline, **write the test as a `pytest.skip` with the
      reason stated** rather than leaving the marker unused. Say in the task report which you did.

- [ ] **Step 7: Run and see them pass**, then the whole suite **excluding slow**
      (`uv run pytest -q -m "not slow"`) and then including it, and report both counts. Expected
      without slow: predecessor's count **+ 3**.

- [ ] **Step 8: Mutate — three.**

  **(a) Install after scaffolding.** Move the `if plugin:` block below `resolve_template`.
  `test_a_failed_plugin_install_scaffolds_nothing` must FAIL on
  `assert not (repo / "src" / "pilot").exists()`. **Checked against the body:** the fake raises, so
  under the mutant the package directory is already created when it does. The ordering test's
  `calls == [...]` assertion would **not** catch this — it only records that the call happened —
  which is why the tree assertion exists.

  **(b) Install unconditionally.** Change `if plugin:` to `if True:`, passing `None` through.
  `test_generate_experiment_installs_the_plugin_before_it_scaffolds` must FAIL on its control's
  `assert calls == []`. **Checked against the body:** the control invokes `generate experiment` with
  no `--plugin` and asserts no call was recorded, so the two branches differ.

  **(c) Write the field from the requirement rather than from the argument.** Change
  `plugin=plugin` to `plugin=plugin_requirement(plugin) if plugin else None`.
  `test_the_plugin_field_carries_what_generate_was_told` does **not** catch this — it calls
  `materialize_config` directly. The CLI test's
  `config["plugin"] == "someuser/publishable-llm"` does. **Named because the obvious target is the
  wrong one**: run the CLI test, not the materialize test, for this mutation.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches.** **Task 6's three document markings being
      reverted is unpinned** — no test reads those cells, as task 6 said. **Nothing closes it**;
      the coupling is this task's commit message, which must name task 6. **`plugin_requirement`'s
      handling of an `@ref` suffix** is pinned only by the materialize test's round trip of the
      *field*, not by an assertion that `git+https://github.com/user/repo@v1` is what `uv` receives
      — add one to the ordering test's first arm if you want it, and say in the report whether you
      did.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: --plugin runs uv add and writes the plugin field — and reverts task 6's markings`

---

