# Task 3 report: `run` writes `<run_dir>/config.yaml` and `environment/repo_root.txt`

Dated 2026-08-20, measured against the commit this task built on (`c834cd1`).

## Status

Done. `command_run` writes two additive artifacts inside the existing `RunLock(run_dir)` block,
right after the shipped `environment/pyproject.toml` / `uv.lock` captures and before `sweep.yaml`
is written — a byte copy of the config (`config_path.read_bytes()`, never a re-dump) and
`environment/repo_root.txt` (`f"{repo_root}\n"`, where `repo_root` is the value `find_repo_root`
already returned — never re-derived from `run_dir`/`output_dir`).

## Code change (`src/publishable/cli.py`)

```
+        # `freeze` (H8b) needs the config as it was and the repo it came from — the
+        # two facts a mid-run command cannot otherwise obtain or compute, since
+        # `run.yaml` embeds the config only once, at the end. A byte copy, never a
+        # re-dump: a re-dump would silently drop every comment `init` wrote.
+        (run_dir / "config.yaml").write_bytes(config_path.read_bytes())
+        (run_dir / "environment" / "repo_root.txt").write_text(f"{repo_root}\n")
```

Two sentences, as required: what the artifacts are for, and what they are not (no claim about a
future reader of `resume`, no safety claim substituting for measurement).

## Arms A and B — the diffs, and the proof each is exactly one appended entry

Task 13's docstrings named the post-edit lists in advance; both match exactly.

```diff
--- test_h8b_arm_a_the_run_directorys_root
     assert sorted(p.name for p in run_dir.iterdir()) == [
         "conditions",
+        "config.yaml",
         "environment",
         "executions.jsonl",
         "manifest",
         "run.yaml",
         "sweep.yaml",
     ]
     assert (run_dir / "lock").exists() is False
```

```diff
--- test_h8b_arm_b_environments_contents
     run_dir = doc["run_dir"]
-    assert sorted(p.name for p in (run_dir / "environment").iterdir()) == ["pyproject.toml"]
+    assert sorted(p.name for p in (run_dir / "environment").iterdir()) == [
+        "pyproject.toml",
+        "repo_root.txt",
+    ]
```

Both diffs (captured with `diff -u` against a pre-edit copy) show exactly one new list element
each — `'config.yaml'` in arm A, in sorted position between `"conditions"` and `"environment"`;
`'repo_root.txt'` in arm B, after `"pyproject.toml"` — with every other element on every line
unchanged and in its original order. Nothing reordered.

## Fixture C (`tests/test_cli.py`, new function)

`test_h8b_fixture_c_run_writes_a_byte_copy_of_the_config_and_the_repo_root`, built per the brief's
mechanism and NOT on `run_a_project` (which rewrites the config with `yaml.safe_dump(doc)`, and
`yaml.safe_dump(yaml.safe_load(x)) == x` is `True` for what it writes — the prescribed mutation
would have been blind there). Instead: `main(["new", …])`, `generate_experiment(...)`, then a raw
text `str.replace` filling `metadata.description` and `metadata.authors` (the two `""`/`[]`
placeholders `init` writes and `validate` requires), preserving every inline comment. Three
assertions:

- `b"#" in cfg.read_bytes()` — the control, proving the byte-equality assertion below is not
  vacuously satisfied by a commentless file.
- `copied.read_bytes() == cfg.read_bytes()` — catches a re-dump.
- `load_document(copied) == run_doc["config"]` — catches a copy taken from a different object.

## Acceptance arm (`tests/test_acceptance.py`)

Added inside `test_scaffold_then_run_produces_a_real_record`, beside the shipped
`environment/pyproject.toml` assertion:

```diff
+    assert (run_dir / "environment" / "repo_root.txt").read_text().strip() == str(root.resolve())
+    config_copy = yaml.safe_load((run_dir / "config.yaml").read_text())
+    assert config_copy["experiment_type"] == doc["config"]["experiment_type"]
```

No path literal — `root.resolve()` is the fixture-built value, never a hard-coded string.

## Mutations run, against the FULL unfiltered suite

**M12 (step 7) — write the config copy with `yaml.safe_dump(doc)` instead of copying bytes.**
Applied as `(run_dir / "config.yaml").write_bytes(yaml.safe_dump(yaml.safe_load(config_path.read_bytes())).encode())`.
Ran `tests/test_cli.py -k test_h8b_fixture_c`: **FAILED**, on the byte-equality assertion
(`copied.read_bytes() == cfg.read_bytes()`), first index diff `b'd' != b'#'` — the dump starts
with `data:` and the original starts with the `# configs/...` comment header. To confirm the
mapping arm is independently satisfied under the same mutation (not merely unreached because the
byte assertion aborted first), I temporarily swapped the two assertions' order and re-ran: the
mapping assertion (`load_document(copied) == run_doc["config"]`) **PASSED** under the mutation,
and the byte assertion still **FAILED** immediately after. Confirmed asymmetric, as the brief
predicted: the dump loses every comment while the parsed mapping still agrees. Reverted by editing
the line back (both the mutation and the temporary reorder); re-ran `-k h8b` — **7 passed**.

**M-additive (step 8) — change the copy's destination to `environment/config.yaml`.** Applied as
`(run_dir / "environment" / "config.yaml").write_bytes(config_path.read_bytes())`. Ran each arm
separately:

- `test_h8b_arm_a_the_run_directorys_root`: **FAILED** — `AssertionError` on the root-list
  equality, `At index 1 diff: 'environment' != 'config.yaml'`, `"Right contains one more item:
  'sweep.yaml'"` — i.e. the actual root list is one entry short of the expected 7-element list
  (`config.yaml` no longer lands at the root), so the lists misalign from index 1 onward.
- `test_h8b_arm_b_environments_contents`: **FAILED** — `AssertionError`,
  `At index 0 diff: 'config.yaml' != 'pyproject.toml'`, `"Left contains one more item:
  'repo_root.txt'"` — the actual `environment/` list gained an entry (`config.yaml`, sorting
  before `pyproject.toml`) beyond the expected two.

The two lists moved in opposite directions, as the brief predicted — arm A lost an entry, arm B
gained one, and neither failure is the other's mirror image, confirming a single-arm pin could not
have distinguished this from "file simply not written." Reverted by editing the path back; re-ran
`-k h8b` — **7 passed**.

## `_files_under` callers — named and run

Grepped `tests/test_cli.py` for `_files_under(` (8 call sites, all inside `results_dir` sweeps).
Traced each call site up to its enclosing `def test_`:

- `test_a_credential_value_reaches_no_artifact_and_the_redaction_says_so`
- `test_a_step_reads_its_credential_and_the_value_still_reaches_no_artifact`
- `test_a_template_exception_printed_as_a_warning_is_redacted_too`
- `test_a_project_local_template_s_credentials_are_redacted_too`
- `test_a_probe_returning_a_declared_credential_fails_the_command_and_writes_no_run_yaml`
- `test_a_fact_value_containing_a_declared_credential_fails_the_command_end_to_end`
- `test_a_probe_that_raises_is_a_redacted_diagnostic_at_run`
- `test_a_probe_that_fails_to_load_is_a_redacted_diagnostic_at_run`

Ran all eight by name (`-k "<names joined by or>"`): **8 passed** — the widened
`_files_under(results_dir)` sweep, now also covering `config.yaml` and `environment/repo_root.txt`,
still finds no credential sentinel in either new artifact.

## Suite delta — attributable to this task alone

Before (stated baseline): 2541 passed, 1 skipped, 2 xfailed.
After (measured, full unfiltered `uv run pytest -q`, run twice at different points in this task,
both `2542 passed, 1 skipped, 2 xfailed` with no failures): **+1 passed, 0 failed, skip/xfail
counts unchanged.**

The +1 is Fixture C, the only brand-new test function this task adds. Arms A and B (task 13's pin)
were edited in place, not added, so they contribute 0 to the count; the acceptance addition is new
assertions inside an already-existing test function, likewise 0. No other test in the full run
failed, so the one net new pass is the only observable change, matching "additive only": no
existing artifact's bytes changed, no verdict/status/exit code/`provenance` key moved (task 13
arm C, arm D never touched; H8a's arm A/arm B, asserting `run.yaml`'s and `provenance`'s key
lists, still pass unedited).

## Gates

- `uv run ruff check .` → All checks passed.
- `uv run ruff format --check .` → 84 files already formatted (unchanged from stated baseline).
- `uv run mypy` → Success: no issues found in 47 source files (unchanged from stated baseline).
- `uv run pytest` → 2542 passed, 1 skipped, 2 xfailed (baseline 2541/1/2 plus this task's one new
  test).

## What I grepped, not a count

Grepped `tests/test_cli.py` for `_files_under(` and traced every call site to its enclosing test
function (list above — 8 functions, all run and reported green). Grepped `src/publishable/cli.py`
for `config.yaml` and `repo_root.txt` before and after the edit to confirm no other site in `src/`
references either new name. Did not grep for or claim zero disagreements elsewhere in the suite;
the only evidence offered for "additive only" is the measured suite delta above and the two named
pins (task 13 arm C/D, H8a arm A/B) that still pass unedited.

## Concerns

None found. Both requirement-3 diffs are exactly one entry each, in sorted position, nothing
reordered. Fixture C's mutation is asymmetric exactly as the plan predicted, ruling out the
blind-mutation failure mode the brief warned about. The scope-widening pin (`_files_under`) was run
by name rather than reasoned about only.
