import os
from pathlib import Path

import pytest

from publishable.secrets import credential_values, load_env, missing_env, redact

_NAME = "PUBLISHABLE_TEST_TOKEN"
_OTHER = "PUBLISHABLE_TEST_OTHER"


# `os.environ` is restored around every test by an autouse fixture in `conftest.py`.
# It lives there because `load_dotenv` writes past `monkeypatch`, and every module
# exercising a load path inherits that hazard.


def test_a_shell_value_wins_over_the_file(tmp_path: Path, monkeypatch):
    """`override=False` is the safety property, not a default that happened to be
    there: a stale `.env` must never silently redirect a run to another account.
    Flipping it is a one-word change, so it is pinned by a test rather than by a
    comment."""
    monkeypatch.setenv(_NAME, "from-the-shell")
    (tmp_path / ".env").write_text(f"{_NAME}=from-the-file\n")

    assert load_env(tmp_path) is True  # the file WAS read — a positive companion
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
    assert load_env(tmp_path) is True  # twice, same answer
    assert credential_values([_NAME]) == {_NAME: "from-the-file"}


def test_no_repo_and_no_file_are_both_quiet(tmp_path: Path, monkeypatch):
    monkeypatch.delenv(_NAME, raising=False)
    assert load_env(None) is False
    assert load_env(tmp_path) is False  # a real directory holding no `.env`
    assert credential_values([_NAME]) == {}


def test_missing_env_answers_in_declared_order_and_dedupes(monkeypatch):
    monkeypatch.setenv(_NAME, "set")
    monkeypatch.delenv(_OTHER, raising=False)
    monkeypatch.delenv("PUBLISHABLE_TEST_AAA", raising=False)
    assert missing_env([_OTHER, _NAME, "PUBLISHABLE_TEST_AAA", _OTHER]) == [
        _OTHER,
        "PUBLISHABLE_TEST_AAA",
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
