## Task 8: The two load sites, and the reconciled single-site sentence

**Files:** Modify `src/publishable/validate.py`, `src/publishable/cli.py`, `docs/reference.md`,
`tests/test_validate.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `load_env(repo_root: Path | None) -> bool` from task 7;
  `validate_config(config_path: Path, c: Collector, *, experiment: Any | None = None) ->
  dict[str, Any] | None`, whose body resolves `repo_root: Path | None` inside a
  `try/except ContractError` before it resolves the template; `cli.command_run(config_path: Path) ->
  int`, which calls `validate_config` and then `repo_root = find_repo_root(config_path)`.
- Produces: `.env` loaded at both sites. **The patch targets tasks 8 and 12 name are
  `publishable.validate.load_env` and `publishable.cli.load_env`** — two different module
  attributes, and a patch on one does not affect the other.

**Why two sites and not one, written down so nobody deletes the second.** `command_run` calls
`validate_config`, so by the time `run` reaches `execute_plan` the environment is already loaded and
the `cli.py` call looks like dead code. It is not: **loading is a precondition of executing, not a
side effect of checking.** A future `run` that skips `validate` — or any executing command that
reaches the runner by another path — must still have the environment. Task 7 made the load
idempotent and non-overriding precisely so the second call costs nothing. Step 4's test is what
stops the deletion.

**`draft` and `resume` are in `cli.NOT_BUILT_COMMANDS`** (together with `dry-run`, `demo`, `diff`,
`docs`, `freeze`, `list-templates`, `plugin new`, `report`, `reproduce`, `study add`, `study new`).
The scoping's § 8 task 8 says the load site is "`run`/`draft`/`resume`"; the buildable set is
**`command_run` alone**. Handle it the way the scoping handled `dry-run`: build the one executing
site, write the document's sentence as what the *specification* says, and record that `draft` and
`resume` inherit the load when they are built. **Do not stub a `command_draft`.**

- [ ] **Step 1: Write the failing tests.**

Append to `tests/test_validate.py`:

```python
def test_validate_loads_dot_env_from_the_repository_root(git_repo: Path, write_config, monkeypatch):
    """`validate` reads `.env`. Not a breach of its promise — `reference.md`
    § Validation promises it "creates nothing and reaches nothing **off the
    machine**", and a file in the repository root is on-machine.

    `delenv` first: `load_dotenv` writes straight into `os.environ` and only
    monkeypatch puts it back.
    """
    import os

    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    (git_repo / ".env").write_text("PUBLISHABLE_TEST_TOKEN=from-the-file\n")

    path = write_config()
    assert codes(path) == set()                      # the config itself is clean
    assert os.environ.get("PUBLISHABLE_TEST_TOKEN") == "from-the-file"

    # THE CONTROL: with no `.env`, the same validate leaves the name unset — so
    # this test fails on a build that never loads rather than passing on a
    # machine that happened to export it.
    (git_repo / ".env").unlink()
    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    assert codes(write_config()) == set()
    assert os.environ.get("PUBLISHABLE_TEST_TOKEN") is None
```

Append to `tests/test_cli.py` — its module-level names are `Ran`, `run_a_project`,
`_AGGREGATE_STEP`, `_TRAIN_TOUCHING_STEP` and the `test_*` functions; `_ENV_READING_STEP` is free:

```python
_ENV_READING_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
import os

from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # Reads the environment directly, which is how `reference.md` § Secrets &
        # credentials says a step gets a credential: core hands it none.
        token = os.environ["PUBLISHABLE_TEST_TOKEN"]
        for unit in io.units:
            io.record(unit.key, {{"present": True}})
        return {{"token_len": len(token)}}
"""


def test_run_loads_dot_env_itself_rather_than_relying_on_validate(tmp_path, monkeypatch):
    """The second load site earns its existence. `publishable.validate.load_env` is
    patched to a no-op — NOT `publishable.cli.load_env`, which is a different
    module attribute and the one under test — so if `command_run` did not load
    for itself, the step's `os.environ[...]` would raise `KeyError` and the
    execution would land `failed`.

    `expect_exit=EXIT_OK` is the assertion: a `KeyError` in the one step makes the
    run `partial`, which is `EXIT_PARTIAL`.
    """
    import publishable.validate as validate_mod

    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    monkeypatch.setattr(validate_mod, "load_env", lambda repo_root: False)

    doc = run_a_project(
        tmp_path, units=4, _starter_step=_ENV_READING_STEP, _env_file="PUBLISHABLE_TEST_TOKEN=abcdefgh\n"
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    per_repeat = run["results"]["conditions"][0]
    # Something that must REPORT, not an absence: the step got the real value and
    # returned its length. 8 is `len("abcdefgh")`, derived from the fixture above.
    assert json.dumps(per_repeat).count('"token_len": 8') >= 1
```

**`run_a_project` needs two new keywords, `_env_file` and `_local_template`**, since it scaffolds
the project itself and nothing outside it can write into `root` before `main(["run", ...])` runs.
Add both in this task — `_env_file` is used here, `_local_template` by **task 12 step 7**, and they
are added together because they are one edit to one signature:

```python
    _env_file: str | None = None,
    _local_template: str | None = None,
```

and, immediately after `assert main(["new", str(root)]) == EXIT_OK` and before the
`pytest.MonkeyPatch.context()` block:

```python
    if _env_file is not None:
        # The scaffold's own `.gitignore` opens with `.env`, so this never reaches
        # the commit below and never makes `src/**`+`templates/**` dirty.
        (root / ".env").write_text(_env_file)
    if _local_template is not None:
        # The opposite property, and it is why this is written HERE rather than
        # after the config is generated: `code_hash` covers `templates/**`, so this
        # file must exist before the `git add .` below or `run` refuses the tree as
        # dirty. Written as `templates/cred_assay.py`, the one name every caller
        # that passes this registers.
        (root / "templates").mkdir(exist_ok=True)
        (root / "templates" / "cred_assay.py").write_text(_local_template)
```

Extend the docstring with one paragraph per keyword, in the same register as its neighbours.
**Do not enumerate their call sites there** — two docstrings in this repo went stale that way and
one is an open `spec-defects.md` gap.

- [ ] **Step 2: Run and see them fail.** The `validate` test fails on
      `os.environ.get(...) == "from-the-file"` (nothing loads). The `cli` test fails with the
      execution having failed on `KeyError` — read the run's `error` field to confirm that is the
      reason, rather than assuming it.

- [ ] **Step 3: Implement.**

In `src/publishable/validate.py`, add to the import block (alphabetical among the
`from publishable.…` imports):

```python
from publishable.secrets import load_env
```

and, inside `validate_config`, immediately after the `try/except ContractError` that resolves
`repo_root` and before the template is resolved:

```python
    # `.env`, once, before any check that asks whether a variable is set.
    # `reference.md` § Validation promises `validate` "creates nothing and
    # reaches nothing off the machine"; a file in the repository root is
    # on-machine, so this is inside that promise rather than an exception to it.
    # Never overrides an exported variable — see `secrets.load_env`.
    load_env(repo_root)
```

In `src/publishable/cli.py`, add `from publishable.secrets import load_env` to the import block and,
in `command_run`, immediately after `repo_root = find_repo_root(config_path)`:

```python
    # The second load site, and it is not redundant. Loading is a precondition of
    # *executing*, not a side effect of checking: `validate` loads because three
    # § Validation rows ask whether a variable is set, and `run` loads because a
    # step is about to read one. Idempotent and never overriding, so the second
    # call costs nothing. `reference.md` § Secrets & credentials.
    load_env(repo_root)
```

- [ ] **Step 4: Run and see them pass.** Both new tests, then the full suite.

- [ ] **Step 5: Reconcile the document.** In `reference.md` § Secrets & credentials, replace "Core
      loads `.env` via `python-dotenv` before any step runs, never reads it into provenance, and
      gitignores it in every scaffold." with:

```
**Core loads `.env` via `python-dotenv` at two moments**, never reads it into provenance, and gitignores it in every scaffold. [`validate`](#validation) loads it because three of its checks ask whether a variable is *set*, and every command that executes loads it again before any step runs, because a step is about to read one — loading is a precondition of executing rather than a side effect of checking. The load never overrides a variable already exported, so a machine supplying its credentials through a secret manager needs no file at all, and a stale `.env` cannot silently redirect a run. **This is not an exception to [`validate`'s promise](#validation)**, which is that it creates nothing and reaches nothing *off the machine*: a file in the repository root is on-machine. In this build the executing site is `run`; [`draft`, `resume` and `dry-run`](#cli-reference) inherit it when each is built.
```

Check that `#validation` and `#cli-reference` both resolve to real headings before committing.

- [ ] **Step 6: Mutate — two.**

  **(a) Delete the `load_env(repo_root)` call in `cli.command_run`.**
  `test_run_loads_dot_env_itself_rather_than_relying_on_validate` must FAIL. **Checked against the
  test body:** it patches `publishable.validate.load_env` to a no-op, so with `cli`'s call gone
  nothing loads, the step raises `KeyError`, the run becomes `partial`, and `run_a_project`'s
  `assert main(...) == expect_exit` fails against the default `EXIT_OK` before the `token_len`
  assertion is even reached. Every `validate` test stays green — which is the point: this mutation
  is the one that proves the second site is load-bearing, and no test written before this task could
  have caught it.

  **(b) Delete the `load_env(repo_root)` call in `validate_config`.**
  `test_validate_loads_dot_env_from_the_repository_root` must FAIL on its
  `os.environ.get(...) == "from-the-file"` assertion. The `cli` test stays green (it patched that
  site away anyway), so the two mutations discriminate the two sites *separately*, which a single
  end-to-end test could not.

  Revert each by editing back; delete `__pycache__`; re-run.

- [ ] **Step 7: Which deliverable no mutation reaches.** The clause "never overrides" is pinned in
      `tests/test_secrets.py` (task 7's mutation (a)) but **not through either wired site** — no test
      here writes a `.env` whose value differs from an exported one and then runs. Accepted:
      `load_env` is the single implementation both sites call, and duplicating the override test at
      each call site would pin the call rather than the behaviour. Named here so it is not
      rediscovered.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: load .env at both sites — validate, and before any step runs`

---

