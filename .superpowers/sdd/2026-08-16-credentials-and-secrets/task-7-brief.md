## Task 7: `secrets.py` and the `python-dotenv` dependency

**Files:** Create `src/publishable/secrets.py`, `tests/test_secrets.py`. Modify `pyproject.toml`,
`uv.lock`, `docs/reference.md` (§ Package layout's marker, deferred from task 6).

**Interfaces:**
- Consumes: `dotenv.load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False,
  interpolate=True, encoding="utf-8") -> bool` — read from `python-dotenv` 1.2.1's `dotenv/main.py`,
  which ships `py.typed`, so **no `mypy` override is expected**. If `uv run mypy` reports a missing
  stub anyway, add `[[tool.mypy.overrides]] module = "dotenv.*"` with
  `ignore_missing_imports = true` in this task and say so in the report — that contingency is named
  here so it is not discovered.
- Produces, all consumed by tasks 8–12:
  - `load_env(repo_root: Path | None) -> bool`
  - `missing_env(names: Iterable[str]) -> list[str]`
  - `credential_values(names: Iterable[str]) -> dict[str, str]`
  - `redact(text: str | None, values: Mapping[str, str]) -> str | None`

**`python-dotenv` is the first runtime dependency this project has added since scaffolding.**
`pyproject.toml` declares `pyyaml`, `numpy`, `scipy`, `pyarrow` today. `code_hash` covers `src/**`
and `templates/**` only, so this disturbs no recorded hash — but it does move `uv.lock`. Version
1.2.1 is already in the local `uv` cache, so `uv add` resolves offline.

- [ ] **Step 1: Add the dependency.** `uv add python-dotenv`. Confirm `pyproject.toml`'s
      `dependencies` now lists it and `uv.lock` moved. Then confirm the import works:
      `uv run python -c "import dotenv; print(dotenv.__version__)"`.

- [ ] **Step 2: Write the failing tests.** Create `tests/test_secrets.py` — a new file, so no
      existing module-level name can be shadowed:

```python
from pathlib import Path

import pytest

from publishable.secrets import credential_values, load_env, missing_env, redact

_NAME = "PUBLISHABLE_TEST_TOKEN"
_OTHER = "PUBLISHABLE_TEST_OTHER"


def test_a_shell_value_wins_over_the_file(tmp_path: Path, monkeypatch):
    """`override=False` is the safety property, not a default that happened to be
    there: a stale `.env` must never silently redirect a run to another account.
    Flipping it is a one-word change, so it is pinned by a test rather than by a
    comment."""
    monkeypatch.setenv(_NAME, "from-the-shell")
    (tmp_path / ".env").write_text(f"{_NAME}=from-the-file\n")

    assert load_env(tmp_path) is True          # the file WAS read — a positive companion
    assert credential_values([_NAME]) == {_NAME: "from-the-shell"}


def test_an_unset_variable_takes_the_file_s_value_and_the_load_is_idempotent(
    tmp_path: Path, monkeypatch
):
    """The honouring half. `delenv` first, because `load_dotenv` writes straight
    into `os.environ` and monkeypatch is the only thing that puts it back."""
    monkeypatch.delenv(_NAME, raising=False)
    (tmp_path / ".env").write_text(f"{_NAME}=from-the-file\n")

    assert load_env(tmp_path) is True
    assert credential_values([_NAME]) == {_NAME: "from-the-file"}
    assert load_env(tmp_path) is True          # twice, same answer
    assert credential_values([_NAME]) == {_NAME: "from-the-file"}


def test_no_repo_and_no_file_are_both_quiet(tmp_path: Path, monkeypatch):
    monkeypatch.delenv(_NAME, raising=False)
    assert load_env(None) is False
    assert load_env(tmp_path) is False         # a real directory holding no `.env`
    assert credential_values([_NAME]) == {}


def test_missing_env_answers_in_declared_order_and_dedupes(monkeypatch):
    monkeypatch.setenv(_NAME, "set")
    monkeypatch.delenv(_OTHER, raising=False)
    monkeypatch.delenv("PUBLISHABLE_TEST_THIRD", raising=False)
    assert missing_env([_OTHER, _NAME, "PUBLISHABLE_TEST_THIRD", _OTHER]) == [
        _OTHER,
        "PUBLISHABLE_TEST_THIRD",
    ]
    # THE CONTROL: with everything set, the answer is empty — so a function that
    # returned its whole argument would fail here rather than only above.
    monkeypatch.setenv(_OTHER, "set")
    monkeypatch.setenv("PUBLISHABLE_TEST_THIRD", "set")
    assert missing_env([_OTHER, _NAME, "PUBLISHABLE_TEST_THIRD"]) == []


def test_an_empty_string_counts_as_unset():
    """A variable exported as the empty string is a name someone wrote down and
    never filled in, which is the fault this family exists to catch — not a
    credential whose value happens to be empty."""
    import os

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv(_NAME, "")
        assert missing_env([_NAME]) == [_NAME]
        assert credential_values([_NAME]) == {}
    assert _NAME not in os.environ  # the context restored it


def test_redaction_replaces_the_exact_value_and_names_the_variable():
    text = "RuntimeError: POST https://api/v1?key=sk-abc123 failed"
    assert redact(text, {"OPENAI_API_KEY": "sk-abc123"}) == (
        "RuntimeError: POST https://api/v1?key=<redacted:OPENAI_API_KEY> failed"
    )
    # By exact value, never by pattern: a string that merely LOOKS like a
    # credential is untouched, because core did not read it out of the
    # environment. This is the fail-closed direction of decision 4.
    assert redact("RuntimeError: token sk-zzzzzz rejected", {"OPENAI_API_KEY": "sk-abc123"}) == (
        "RuntimeError: token sk-zzzzzz rejected"
    )
    assert redact(None, {"OPENAI_API_KEY": "sk-abc123"}) is None
    assert redact("nothing to do", {}) == "nothing to do"


def test_a_value_that_contains_another_value_is_redacted_whole():
    """Longest first. With `SHORT` applied before `LONG`, the longer value is left
    half-exposed as `<redacted:SHORT>def` — a leak that reads as a redaction.
    Two credentials where one value is a prefix of the other is the only fixture
    that can tell the two orders apart."""
    values = {"SHORT": "abc", "LONG": "abcdef"}
    assert redact("saw abcdef here", values) == "saw <redacted:LONG> here"
    assert redact("saw abc here", values) == "saw <redacted:SHORT> here"
```

- [ ] **Step 3: Run and see it fail.** `uv run pytest tests/test_secrets.py -q` —
      `ModuleNotFoundError: No module named 'publishable.secrets'`.

- [ ] **Step 4: Implement.** Create `src/publishable/secrets.py`:

```python
"""`.env` loading and the credential values core read.

docs/reference.md § Secrets & credentials. A config holds an environment
variable's NAME; the value lives in `.env`, which every scaffold gitignores.

**Never touches provenance**, and the claim is structural rather than careful:
nothing in this module imports `publishable.provenance` or writes into the
document it builds, and `provenance.environment` is assembled from `os`,
`hostname`, `hardware` and `uv.lock` alone. The one surface on which a value
could reach a record is a failing step's exception text, which `redact` below
exists for.
"""

import os
from collections.abc import Iterable, Mapping
from pathlib import Path

from dotenv import load_dotenv

ENV_FILENAME = ".env"


def load_env(repo_root: Path | None) -> bool:
    """Load `<repo_root>/.env` into `os.environ`. Returns whether a file was read.

    **Never overrides.** `override=False` means a variable already exported in the
    shell wins over the file, which is the direction that fails safe: a stale
    `.env` cannot silently redirect a run to the wrong account, and a machine that
    supplies its credentials through a secret manager needs no file at all.

    Idempotent, because it is called twice on a `run` — once by `validate` and
    once before any step executes — and a second load with `override=False` can
    only re-set what is already set.

    A `None` root (no git repository) and a directory holding no `.env` are both
    quiet: a project whose credentials are exported rather than filed is ordinary,
    and this function has no way to tell it from one that forgot. Whether a
    *declared* variable is missing is `missing_env`'s question, asked by
    `validate` against what a template declares.
    """
    if repo_root is None:
        return False
    path = repo_root / ENV_FILENAME
    if not path.is_file():
        return False
    return load_dotenv(path, override=False)


def missing_env(names: Iterable[str]) -> list[str]:
    """Declared names with no value, in declared order, each named once.

    An empty string counts as missing: a name exported with no value is one
    somebody wrote down and did not fill in, which is the fault this family
    exists to catch.
    """
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        if not os.environ.get(name):
            out.append(name)
    return out


def credential_values(names: Iterable[str]) -> dict[str, str]:
    """The values core read for the declared names — `{name: value}`, unset omitted.

    This is the knowledge `redact` answers from, and the whole of decision 4: core
    can say *is this the value I read out of the environment* rather than *does
    this look like a secret*. A pattern check fails open on a credential named
    `instrument_pw` and fails closed on a config value that happens to look
    random.

    Held only for the length of one command, and never written anywhere: the
    mapping is built where a run starts and reaches exactly one consumer.
    """
    found: dict[str, str] = {}
    for name in names:
        value = os.environ.get(name)
        if value:
            found[name] = value
    return found


def redact(text: str | None, values: Mapping[str, str]) -> str | None:
    """Replace each credential value in `text` with a marker naming its variable.

    Longest value first, so a credential whose value is a prefix of another's
    cannot leave the longer one half-exposed as `<redacted:SHORT>def` — which
    would read as a redaction while being a leak.

    Says a redaction happened rather than scrubbing silently: the record exists to
    be debugged from, and `<redacted:OPENAI_API_KEY>` tells a reader both what was
    removed and which variable to look at, without telling them the value.
    """
    if not text or not values:
        return text
    for name, value in sorted(values.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if value:
            text = text.replace(value, f"<redacted:{name}>")
    return text
```

- [ ] **Step 5: Run and see it pass.** `uv run pytest tests/test_secrets.py -q`, then the full suite:
      **1957 + task 3's 5 + task 4's 2 + these 7 = 1971 passed, 2 xfailed** (adjust for what actually
      landed; the point is that nothing existing broke). `uv run mypy` must be clean.

- [ ] **Step 6: Mutate — three.**

  **(a) `override=False` → `override=True`.** `test_a_shell_value_wins_over_the_file` must FAIL:
  `credential_values` would return `from-the-file`. **Checked against the test body:** it sets the
  shell value with `monkeypatch.setenv` *before* writing a different value into the file, and
  asserts on the resolved value, so the two branches genuinely differ.

  **(b) Drop the longest-first sort.** Change `sorted(values.items(), key=...)` to
  `values.items()`. `test_a_value_that_contains_another_value_is_redacted_whole` must FAIL — insertion
  order puts `SHORT` first, so `"saw abcdef here"` becomes `"saw <redacted:SHORT>def here"`.
  **Checked:** the fixture is a dict literal with `SHORT` written first, so the mutant's order is
  deterministic and different. Without that fixture this mutation would be blind, which is why the
  test exists.

  **(c) Treat an empty string as set.** Change `if not os.environ.get(name):` to
  `if os.environ.get(name) is None:` in `missing_env`. `test_an_empty_string_counts_as_unset` must
  FAIL.

  Revert each by editing back; delete `__pycache__`; re-run.

- [ ] **Step 7: Which deliverable no mutation reaches — say it plainly.** The docstring's **"never
      touches provenance"** claim is a safety claim, and `CLAUDE.md` is explicit that a safety
      argument in a comment needs a mutation like any other. **No mutation in this task reaches it**,
      because at this commit nothing calls `secrets.py` at all: there is no run for a value to leak
      into. **Task 12 closes it** — its sweep covers `run.yaml`, which embeds the whole `provenance`
      block, and its mutation (deleting the redaction call) makes that sweep go red. Do not
      substitute a source-text assertion (`"provenance" not in inspect.getsource(...)`) here; that
      is a proxy for the fact, which is exactly the move `CLAUDE.md` § Answering a question with a
      proxy records as twice-burned.

- [ ] **Step 8: Execute task 6's deferred step.** In `docs/reference.md` § Package layout, retire
      `secrets.py`'s marker so the line reads:

```
│   ├── secrets.py             # dotenv loading, required_env checks (never touches provenance)
```

Then confirm the surrounding paragraph ("**Modules marked `— not yet built` are specified and
unbuilt.**") still describes a non-empty set — `apparatus.py`, `reproduce.py`, `report.py` remain —
and run the mechanical pass over the fenced tree block (it is a code fence, so the anchor and table
checks do not apply; check alignment and whitespace only).

- [ ] **Step 9: Verify and commit.** All four commands.
      `feat: secrets.py — .env loading, the values core read, and redaction by exact value`

---

