# Task 5 report

**Status:** done.

Added `tests/test_cli.py::test_a_one_segment_parameter_spec_path_through_the_console_script_is_a_diagnostic`
and `..._three_segment_...`, running `validate` in a real subprocess
(`sys.executable -c "...from publishable.cli import main..."`, the `test_h9b_*`
idiom) against a committed project with a broken `templates/broken.py`. Each
asserts exit `1` (`EXIT_WRONG`), `E-TEMPLATE-PARAM-PATH` in stdout, and the
literal `Traceback (most recent call last):` absent from both streams.

**Mutation evidence** (`src/publishable/templates/base.py:83`,
`path.count(".") != 1`):
- `< 1`: `pytest tests/test_cli.py -k parameter_spec_path_through_the_console_script -q` → `1 failed, 1 passed` — three-segment arm failed (`E-TEMPLATE-PARAM-PATH` absent, config fell through to `E-META-REQUIRED` findings instead), one-segment arm still passed.
- `> 1`: same command → `1 failed, 1 passed` — one-segment arm failed, three-segment arm passed (mirror image, confirmed in-session before the ruff line-length fixup, same check re-run below).
- Restored to `!= 1`: same command → `2 passed, 575 deselected` — verified green by re-running the tests (not by `git status`); `git diff --stat` on `base.py` also shows no diff.

**Concerns:** none. `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy` all pass.
