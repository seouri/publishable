# Task 7 report: `secrets.py` and the `python-dotenv` dependency

**Status:** done. **Commit:** `b907ab6` on branch `h7c-credentials`.

**Tests:** `uv run pytest -q` → **1971 passed, 2 xfailed** (matches the brief's prediction exactly).
`uv run ruff check .` and `uv run ruff format --check .` clean (76 files formatted, including the
two new ones). `uv run mypy` clean, **no `dotenv.*` override needed** — 1.2.x ships `py.typed` and
`load_dotenv`'s signature matched the brief verbatim.

## Disagreements between the brief/spec and the code

1. **Dependency version.** The brief said 1.2.1 was the cached version `uv add` would resolve to.
   `uv add python-dotenv` (offline, no network hit) resolved to **1.2.3** instead — 1.2.1, 1.2.2, and
   1.2.3 are all present in the local `uv` cache (`~/.cache/uv/archive-v0/*/python_dotenv-1.2.*`), and
   `uv add` without a pin takes the newest satisfying one. `pyproject.toml` now reads
   `python-dotenv>=1.2.3`. I checked `load_dotenv`'s actual signature under 1.2.3 against the one
   quoted in the brief — identical, including `interpolate` and `encoding="utf-8"` — so nothing
   downstream is affected, but the brief's specific version claim was stale.

2. **The verbatim test file leaks environment state across tests, independent of anything I wrote.**
   `load_env` → `load_dotenv(path, override=False)` writes directly into `os.environ`, bypassing
   `monkeypatch` (which only undoes changes made *through* `monkeypatch.setenv`/`delenv`). Running the
   brief's test file exactly as given, in file order:
   `test_an_unset_variable_takes_the_file_s_value_and_the_load_is_idempotent` sets `_NAME` to
   `"from-the-file"` via `load_env`, and that value survives past the test (monkeypatch never captured
   it). It later collides with `test_an_empty_string_counts_as_unset`, whose
   `assert _NAME not in os.environ` fails because the leaked value is still there. This reproduced
   before any mutation and before my implementation touched anything — it's a property of dotenv
   writing straight into `os.environ` plus the given fixtures, not of `secrets.py`'s logic. I added
   an `autouse` fixture in `tests/test_secrets.py` (infrastructure, not a change to any given test
   body) that snapshots and restores `os.environ` around each test in the file. This is exactly the
   direction `CLAUDE.md`'s "environment is inherited" warning and the brief's own framing point at —
   I verified the failure first, then added the minimal fix rather than editing the test bodies.

## The `— not yet built` marker

Retired in this commit, in `docs/reference.md` § Package layout: the `secrets.py` tree line now reads
`# dotenv loading, required_env checks (never touches provenance)` with no trailing marker. Confirmed
the surrounding paragraph ("Modules marked `— not yet built` are specified and unbuilt") still
describes a non-empty set: `apparatus.py`, `reproduce.py`, `report.py` all still carry the marker,
plus `plugin_scaffold.py`, `docs.py`, `lineage.py`, `study.py` elsewhere in the same tree. Alignment
and trailing whitespace checked directly on the diff — no other line in the fenced block moved.

## The "never touches provenance" claim

Not pinned end-to-end at this commit, and I'm saying so rather than proving it with a proxy. Nothing
calls `secrets.py` yet — there is no run for a value to leak into, so no mutation in this task can
reach the claim. I did not substitute `"provenance" not in inspect.getsource(...)` or any similar
source-text check; per the brief (and `CLAUDE.md` § Answering a question with a proxy, which records
this exact move as twice-burned already), that would answer a different, correlated question rather
than the actual one. Task 12 closes it: its leak sweep covers `run.yaml` (which embeds the whole
`provenance` block), and its mutation — deleting the redaction call — is what has to make that sweep
go red.

## Mutations (all reverted by editing the file back, `__pycache__` cleared, revert confirmed by
re-running the test — never by `git status`)

**(a) `override=False` → `override=True`.**
Checked first: `test_a_shell_value_wins_over_the_file` sets the shell value via `monkeypatch.setenv`
*before* writing the file, and asserts on the resolved value — the two branches genuinely differ.
Result: **FAIL**, exactly that test —
`AssertionError: {'PUBLISHABLE_TEST_TOKEN': 'from-the-file'} != {'PUBLISHABLE_TEST_TOKEN': 'from-the-shell'}`.

**(b) Drop the longest-first sort** (`sorted(values.items(), key=...)` → `values.items()`).
Checked first: the fixture `{"SHORT": "abc", "LONG": "abcdef"}` is a dict literal with `SHORT` first,
so insertion order and the mutant's iteration order are the same and differ from sorted order.
Result: **FAIL**, `test_a_value_that_contains_another_value_is_redacted_whole` —
`'saw <redacted:SHORT>def here' != 'saw <redacted:LONG> here'`.

**(c) Treat an empty string as set** (`if not os.environ.get(name):` → `if os.environ.get(name) is None:`).
Result: **FAIL**, `test_an_empty_string_counts_as_unset` — `assert [] == ['PUBLISHABLE_TEST_TOKEN']`.

All three discriminated correctly; none needed prescribing a different mutation.

## What the mutation set does not reach

Per Step 7, and confirmed above: the docstring's "never touches provenance" claim has zero mutation
coverage at this commit, because nothing calls this module yet. Named explicitly rather than left
implicit — task 12 owns closing it.

## Corrections (task 7 review, 2026-08-16)

1. **`missing_env`'s declared-order guarantee was pinned by nothing.** The fixture names were already
   alphabetical, so declared order and sorted order were the same answer and `return sorted(out)` left
   all seven tests green — while the test's own NAME claimed the guarantee, which would have sent task
   9's implementer looking no further. A fixture name was changed so the two orders differ, and the
   mutation now fails exactly that test. Proven both ways.
2. **The isolation fixture moved to `tests/conftest.py`.** The leak it works around is real and was
   reproduced, but the fixture was file-local while every module exercising a load path inherits the
   same hazard — tasks 8–12 would each have rediscovered it. Proven load-bearing after the move:
   flipping `autouse` to `False` reproduces the failure, restoring it passes.
3. **`load_env`'s "Returns whether a file was read" was false.** Measured: a comment-only `.env`
   returns `False`, an empty one returns `False`, and a load whose every binding is skipped because
   the shell already set it returns `True`. The docstring now says what the value is and that no
   caller depends on the distinction.
