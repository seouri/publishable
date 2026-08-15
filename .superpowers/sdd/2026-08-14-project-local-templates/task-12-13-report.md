## Tasks 12–13: status report

**Status:** both done.

**Commits (rewritten after coordinator correction, see below — `c4a5224`/`322129e` no longer exist):**
- `645b4a4` — docs: split register_template from the unbuilt registries row (task 12)
- `a0d2ab6` — docs: add discovery.py to § Package layout's source tree (task 13)

**Test summary:** `uv run pytest` → 1681 passed, 2 xfailed (matches baseline); `uv run ruff check .` → all checks passed; `uv run mypy` → no issues found in 42 source files.

**Concerns:** none. `register_resolver`/`register_probe`/`register_writer` confirmed still `ImportError` via direct import; `register_template` confirmed importable. `discovery.py` confirmed as its own file (not folded into `registry.py`), so it was added to the tree rather than skipped. Grepped for the old unsplit row string and the old `templates/{...}` tuple without `discovery.py` — neither remains anywhere in tracked docs. No other "four plugin registries" count phrase needed touching (the "Four registries, one mechanism." line in § Creating a plugin describes the four entry-point groups, unaffected by this split).

### Correction: task 12's `ImportError` paragraph should not have been rewritten

My first pass hardcoded the five currently-unbuilt names (`BaseReport`, `Apparatus`, `register_resolver`, `register_probe`, `register_writer`) into the prose paragraph below the table. The coordinator caught this: the original sentence — "Importing one raises `ImportError` today" — derives its truth from the `Status` column rather than restating it, so splitting the row alone repairs it; no textual change was needed. My rewrite introduced a second source of truth for build state (the enumerated name list), which drifts the moment the `Status` column changes again — e.g. when H7b ships `register_resolver`, someone would have to remember to also edit this sentence, and nothing enforces that. It also embedded an undated build fact (`register_template` moved off this list once it shipped`) in prose, where the `Status` column is this table's sanctioned place for build state.

Fixed by reverting the paragraph to its exact original wording (confirmed via `git diff e99e50f a0d2ab6 -- docs/reference.md`, which now shows only the row split and the `discovery.py` addition — the paragraph is untouched relative to the pre-task-12 baseline). Rather than amend a non-tip commit, I did `git reset --soft e99e50f` (recoverable, not destructive — both prior commits stayed reachable via reflog until the reset), then re-split the combined working-tree diff into two clean commits by temporarily reverting the `discovery.py` line for the first commit and reapplying it for the second. Re-ran the full mechanical pass (no trailing whitespace/tabs introduced) and all three verification commands after the fix; all clean, matching baseline.

I don't believe an enumeration earns its keep here: a reader gets nothing from a hardcoded name list that the `Status` column two rows above doesn't already give them, and no mechanism updates it when the next registry ships.
