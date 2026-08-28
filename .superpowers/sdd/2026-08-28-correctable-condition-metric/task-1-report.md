# Task 1 report — the bit-stability oracle

Status: done. Commit: 2ddcacb.

Added `test_task1_bit_stability_oracle_over_the_correction_machinery` to
`tests/test_cli.py`, following the H9a/H9b golden-record idiom
(`_h9a_run_yaml_leaves`) rather than inventing a second one. The fixture:
three-condition sweep (`baseline: pearson`, `grid: [spearman, kendall]`),
`statistics.resample: {bootstrap, n: 500}`, a declared
`statistics.contrasts` entry, the config's default `statistics.correction:
holm`, and one confirmatory `evaluate_on: ci95_lower` hypothesis with
`compare: {to: baseline}` (never `to: constant`, since that combination is
what this slice may still change). Verified before pinning: `vs_baseline`,
`contrasts`, and `hypotheses.observed` all carry non-null `ci95_corrected`
and `family_size == 3`.

Normalization is entirely delegated to `_h9a_run_yaml_leaves` (hashes,
timestamps, wall seconds, run id, host facts, tmp-path-containing strings).
One value that embeds a hash as text, `results.hypotheses.0.declared_in`,
was checked rather than assumed stable: two fully independent captures
(separate tmp dirs, separate git commits) produced byte-identical leaves
lists, so it is pinned as a literal.

Mutation evidence: changed one golden literal
(`results.contrasts.0...ci95_corrected.0` from `0.8250000000000028` to
`9.9999999999999`) — test failed with `AssertionError: ... At index 226
diff: (...0.825...) != (...9.999...)`. Restored via `cp` from a pre-mutation
backup (verified identical by `diff`, and by re-running the test, not by
`git status`) — test passed again: `1 passed, 582 deselected`.

Verification commands run:
- `uv run pytest tests/test_cli.py -k test_task1_bit_stability_oracle_over_the_correction_machinery -q` → `1 passed, 582 deselected`
- `uv run ruff check .` → `All checks passed!`
- `uv run ruff format --check .` → `101 files already formatted`
- `uv run mypy` → `Success: no issues found in 56 source files`

No production code touched. Only `tests/test_cli.py` changed plus this
report.

Concern to report, not fixed: the brief pins the run at commit `b3d1d06`;
the session instructed working at current HEAD (`b5eb0ef`, one commit
ahead — a G2 correction, docs-only). The oracle was captured against
`b5eb0ef` per the controller's explicit instruction.
