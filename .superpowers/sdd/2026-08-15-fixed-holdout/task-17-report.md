# Task 17 report

**Status:** done.

**Commit:** `5eaaddb` — feat: allocation.json records the realized holdout split.

**Test summary:** `uv run pytest` — 1950 passed, 2 xfailed (1945 passed + 2 xfailed before, +5 new tests in `tests/test_artifacts.py`, all passing). `uv run ruff check .` clean, `uv run mypy` clean (42 source files). `uv run ruff format --check` on only the three touched files shows one pre-existing unrelated diff each in `artifacts.py` and `cli.py` (far from anything this task touched, present identically on the pre-task commit via `git stash`); `tests/test_artifacts.py` is clean after fixing the one line ruff flagged in my own addition.

## The three consumers named in task 13's `_resolved_holdout` docstring

All three now exist and are handed the same `holdout_plan` object from `cli.command_run`:

1. **The denominators** — `eval_roster = _evaluation_roster(roster, holdout_plan)` (`src/publishable/cli.py:1522`).
2. **The runner's narrowing** — `holdout_train=(UnitList([...]) if holdout_plan is not None ...)` passed into `execute_plan` (`src/publishable/cli.py:1657-1660`).
3. **`build_allocation_document`** — `alloc_doc = build_allocation_document(group_axes, holdout_plan)` (`src/publishable/cli.py:1641`), landed by this task.

The docstring's present-tense claim is now true and needed no correction.

## Four mutations run (brief's three plus the fourth I added)

All reverted by editing the file back (never `git checkout --`), each revert verified by re-running the test, and a final `diff` against a pre-mutation backup copy confirmed the file is byte-identical to the pre-mutation state.

- **(a)** Gate `if not group_axes and holdout is None:` → `if not group_axes:`. `test_the_document_is_written_when_either_partition_is_declared` **FAILED** (`build_allocation_document({}, plan) is not None` → got `None`). Reverted, re-ran, passes.
- **(b)** `if holdout.seed is not None: block["seed"] = ...` → `block["seed"] = holdout.seed` unconditionally. `test_a_read_holdout_records_neither_seed_nor_strata` **FAILED** (extra `'seed': None` key present). Reverted, re-ran, passes.
- **(c)** Swapped `block["train"]`/`block["test"]` to `list(holdout.test)`/`list(holdout.train)`. `test_the_allocation_hash_covers_the_holdout_block`'s inequality assertion **still PASSED** (both documents move together, so the hash difference persists), while `test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block` **FAILED** (`train`/`test` values swapped in the membership assertion). Both outcomes are the point — a hash test cannot see a swap symmetric across its two inputs. Reverted, re-ran, passes.
- **(d)** `if holdout.strata: block["strata"] = ...` → `block["strata"] = list(holdout.strata)` unconditionally. `test_a_drawn_unstratified_holdout_records_its_seed_and_no_strata` **FAILED** (extra `'strata': []` key present, where the expected document has no `strata` key at all). Reverted, re-ran, passes. This arm was distinguished correctly by the brief's own assertion style (exact dict equality) — no stronger assertion was needed.

## Where the brief disagreed with the code

**Key order.** `docs/reference.md` § `allocation.json`'s printed example (settled in task 2) orders the four top-level keys `seed`, `arms`, `holdout`, `strata`. The brief's literal Step 3 code builds `document = {"seed": seed, "arms": arms, "strata": strata}` and then does `document["holdout"] = block` afterward — since Python dicts preserve insertion order and `json.dumps(..., indent=2)` follows it, that produces `seed, arms, strata, holdout`, one position off from the document. I built the dict as `{"seed": seed, "arms": arms}`, inserted `"holdout"` conditionally, then set `document["strata"] = strata` last, which reproduces `seed, arms, holdout, strata` exactly — verified by running `build_allocation_document` directly and printing `json.dumps(doc, indent=2)` against the brief's own example values (`P0002`/`P0007`/`P0011`/`P0019`, seed `3310985422`, `strata: ["label"]`), which matches § `allocation.json`'s fenced JSON key-for-key. Per Step 4's own instruction ("confirm the written file's key order matches what task 2 printed, or fix one of the two"), the code was the one to fix since the document shape was already settled and easy to match.

No other disagreement found — the gate, payload, docstring replacement, and the cli.py call-site/comment changes matched the brief as given, and all four of the brief's own test functions (plus the fourth I added per the task instructions) pass unmodified from the brief's literal text (aside from one cosmetic line-length fix `ruff format` wanted in my own new test, unrelated to logic).

## Housekeeping noted and fixed

`.superpowers/sdd/.gitignore` had been clobbered to a bare `*` before this session started (the known `scripts/sdd-workspace`/`task-brief` side effect CLAUDE.md warns about). Restored its tracked content from `HEAD` before doing any work in that tree, per CLAUDE.md's instruction to restore it when noticed. Nothing else in `.superpowers/sdd/` needed re-adding since no new task records were created before the restore.

## Concerns

None outstanding. `docs/reference.md` needed no edits — it already documented the four-key shape (settled in task 2) and the implementation now matches it exactly, including key order. `spec-defects.md` has no open item naming this task.
