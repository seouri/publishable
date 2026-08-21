# Task 3 review — `run` writes the config copy and the recorded repo root

Reviewed 2026-08-20 against commit `6335c1d` on `h8b-diff-freeze`, parent `c834cd1`. Everything
below marked **verified by running** was run in this worktree; everything else says it was read.

## Verdicts

- **Spec compliance: PASS.** Decision 7 is implemented as ruled — a byte copy of the config at the
  run-directory root, `environment/repo_root.txt` holding the absolute repo root `command_run`
  already computed, both inside the existing `RunLock` block before `sweep.yaml`. All three
  requirements the controller attached are met.
- **Task quality: PASS with findings.** Four Minors, all in the report's own evidence and one
  count phrase in a shipped docstring. Nothing in the code is wrong.

## Requirement 1 — additive-only, pinned in two directions

**Verified by running, not by reading the suite delta.** I built the same project twice — once at
`6335c1d`, once in a throwaway worktree at `c834cd1` — through an inline scaffold + `generate_experiment`
+ `main(["run", …])`, and compared the two run directories in full.

- **File lists differ by exactly two entries**: `./config.yaml` and `./environment/repo_root.txt`.
  `diff -r` over the whole tree reports no third addition and no deletion.
- `results_dir`'s own listing (the `latest` symlink and the run directory) is identical.
- Exit code **0** on both.
- Equal across both records: the `run.yaml` top-level key list (all 11, same order), the
  `provenance` key list (all 13, same order), `status` (`completed`), `draft`, `schema_version`,
  `parameters_hash`, `code_hash`, `layout`, `results`, `units_hash`, `allocation_hash`,
  `provenance.apparatus` (`None` both), `provenance.upstream` (`[]` both), and `sweep.yaml` parsed
  in full. `execution` is equal after stripping `started_at`/`wall_seconds`.
- The only remaining differences are incidental to running twice in two directories: `run_id`,
  timestamps, `wall_seconds`, the fixture's `input_dir`/`output_dir`/`repo_root`, the fixture repo's
  own commit sha, `manifest/input.json`'s `mtime`, and the `input_manifest_hash` computed over it.
  `parameters_hash` is **identical** despite the differing `input_dir`/`output_dir`, which is the
  projection behaving as documented.
- `config.yaml` in the run directory is byte-identical to the source config (`cmp`, exit 0);
  `environment/repo_root.txt` is the one absolute line.

**Read, to close the inertness claim over all of `src/` rather than one file:** `grep -rn
'iterdir\|rglob\|\.glob('` over `src/publishable/` returns nine sites, none of which iterates a run
directory — `manifest.py` and `units.py` walk `input_dir`, `hashes.py` walks `src/**`+`templates/**`
under `repo_root`, `scaffold.py`/`plugin_scaffold.py`/`validate.py` test emptiness of a scaffold or
`input_dir`/`output_dir`, `templates/discovery.py` walks `templates/`, `generators/step.py` walks
`steps/`. `lineage.py`'s only run-directory access appends `run.yaml` to the directory.

**Also verified by reading, and outside the brief's ten steps:** Decision 7 says `run` *and* `draft`
*and* `resume` write these. `draft` and `resume` are both in `NOT_BUILT_COMMANDS`
(`src/publishable/cli.py:150,156`) and `command_run` is the only `def command_*` that creates
`environment/` (`cli.py:2338` is the sole `(run_dir / "environment").mkdir()` in `src/`), so the
parenthetical is satisfied and no half of Decision 7 was shipped.

## Requirement 2 — the document was not re-opened

**Verified.** `git show --stat 6335c1d` touches four files: `src/publishable/cli.py`,
`tests/test_acceptance.py`, `tests/test_cli.py`, and this task's report. **No `docs/` file.**

**Doc-vs-code agreement, read:** `docs/reference.md` § Run identity's tree shows `config.yaml` at the
run root and `repo_root.txt` inside `environment/{…}`; § The other files a run writes calls both
"settled before the first execution and never touched again"; § `config.yaml` and
`environment/repo_root.txt` says byte copy, one line, written at run start beside
`environment/pyproject.toml`. All four claims match `cli.py:2351-2352` exactly, including the
placement before `sweep.yaml` and inside the lock. § The two files was checked as the ruling
required and carries the paragraph explaining why it is not renamed — landed by task 14, untouched
here.

## Requirement 3 — the authorized pin edit, audited

**Verified by diffing `c834cd1..6335c1d` over `tests/test_cli.py` line by line.** Across both arms
the diff is **one added line in arm A** (`"config.yaml",`, in sorted position between
`"conditions"` and `"environment"`) and, in arm B, one single-line list replaced by the same list
plus one entry (`"pyproject.toml", "repo_root.txt"`) reflowed across lines because the one-line form
exceeds the line limit. **Nothing reordered, no element removed, no docstring touched** — the
post-edit lists task 13 stated in advance are exactly what landed. No other arm's assertions appear
in the diff.

**Both arms still discriminate — verified by running three mutations, each reverted by editing back
from a kept copy and confirmed by behaviour:**

| Mutation | Arm A | Arm B | Fixture C |
|---|---|---|---|
| destination → `environment/config.yaml` | **FAIL** `At index 1 diff: 'environment' != 'config.yaml'` … `Right contains one more item: 'sweep.yaml'` (root list one short) | **FAIL** `At index 0 diff: 'config.yaml' != 'pyproject.toml'` … `Left contains one more item: 'repo_root.txt'` (`environment/` one long) | FAIL |
| delete the `config.yaml` write | **FAIL** | pass | FAIL |
| delete the `repo_root.txt` write | pass | **FAIL** | FAIL |
| a stray `zz_probe.txt` beside the two writes | **FAIL** | pass | pass |

The report's claimed opposite-direction failure reproduces verbatim. Rows 2 and 3 are the stronger
test the report did not run: each arm fails **alone** on its own missing entry, so neither is
carried by the other. Row 4 closes the remaining direction — the criterion was *stray or missing* on
both arms, and the destination move made arm A **lose** an entry rather than gain one, so arm A's
stray direction needed its own mutation. It fails on the extra element. **All four directions
demonstrated by running; none inferred.**

## The blind-mutation rebuild — both halves reproduced

**Verified by running.** Fixture C is built on a raw scaffold-and-run (`main(["new"])` →
`generate_experiment` → two `str.replace` edits filling `metadata.description`/`authors` → commit →
`main(["run"])`), never on `run_a_project`, and carries the `b"#" in cfg.read_bytes()` control.

- **M12** (`write_bytes(yaml.safe_dump(yaml.safe_load(config_path.read_bytes())).encode())`): the
  byte arm fails — `assert b"data:\n  in…" == b'# configs/c…'`, `At index 0 diff: b'd' != b'#'`.
- **The asymmetry, isolated rather than inferred:** with the two assertions' order temporarily
  swapped under the same mutation, `load_document(copied) == run_doc["config"]` **passes** and the
  byte assertion fails immediately after. Predicted asymmetry confirmed.
- **The mapping arm is not vacuous** — an extra check the brief did not ask for. Under a mutation
  appending `zz_extra: 1` to the copy, with the order swapped, the mapping assertion fails on
  `Left contains 1 more item: {'zz_extra': 1}`. So each arm can fail on its own.

`tests/test_cli.py` was restored from a kept copy and confirmed byte-identical.

## The acceptance additions are pinned too

**Verified by running.** Every mutation above was selected over `test_cli.py`, so the two assertions
added at `tests/test_acceptance.py:90-92` were shown green only in the unmutated state — the "correct
fix shipped unpinned" shape the ledger counts five of. I ran both deletion mutations against
`test_scaffold_then_run_produces_a_real_record` on its own:

- delete the `config.yaml` write → **FAILED**, `FileNotFoundError … /results/run_…/config.yaml`.
- delete the `repo_root.txt` write → **FAILED**, `FileNotFoundError … /environment/repo_root.txt`.

Both new assertions therefore carry real power, independently of `test_cli.py`'s arms.

## The widened credential sweep — enumeration re-measured, and the affirmative half run

**Verified by running.** `grep -rn '_files_under' tests/ src/` (repo-wide, not one file) finds the
definition at `tests/test_cli.py:11122` and **exactly 8 call sites** at lines 11192, 11225, 11290,
11357, 13166, 13204, 13244, 13541, in **8 distinct** test functions — the same eight the report
names, and there is no ninth anywhere in `tests/` or `src/`. `_files_under` is
`rglob("*")` + `is_file()` with **no suffix filter**, and each caller reads every path's bytes and
decodes with `errors="replace"`, so no artifact can be silently skipped.

**The affirmative measurement the report did not take.** I injected the credential value into each
new artifact in turn and re-ran all eight:

- credential appended to `environment/repo_root.txt` → **6 of 8 FAIL** on the sweep.
- credential appended to `config.yaml`'s bytes → **6 of 8 FAIL** on the sweep.

The two that pass in both cases are `test_a_template_exception_printed_as_a_warning_is_redacted_too`
and `test_a_project_local_template_s_credentials_are_redacted_too`, which set
`PUBLISHABLE_TEST_TOKEN=irrelevant` and put `_SENTINEL` in a different variable
(`PUBLISHABLE_TEST_AZURE`) — so they were never expected to fire on the variable I injected. Both
new artifacts are genuinely inside the swept set. Baseline before the injections: **8 passed.**

(Disclosure: my first attempt at this mutation was invalid — `os` is not imported in `cli.py`, so
all eight failed with `NameError`. I caught it by reading the failure text rather than the count, and
redid it with a local import. A count alone would have looked like a pass.)

## Findings

### Minor 1 — the report's `src/` claim is false as worded

`.superpowers/sdd/2026-08-20-diff-freeze/task-b3-report.md`, § *What I grepped, not a count*:
*"Grepped `src/publishable/cli.py` for `config.yaml` and `repo_root.txt` … to confirm no other site
in `src/` references either new name."* The grep was over one file; the claim is over `src/`.
**Verified by running** `grep -rn 'config.yaml' src/publishable/`: two other sites reference the
name — `src/publishable/materialize.py:108` (`f"# configs/{name}/config.yaml"`, the header comment
`init` writes) and `src/publishable/generators/experiment.py:145`
(`repo_root / "configs" / name / "config.yaml"`). **Verified by reading** both: neither resolves a
name relative to a run directory, so the conclusion holds and nothing is broken — but the stated
evidence does not establish it, and the sentence as written is untrue. This is CLAUDE.md's *sweep for
the claim, not for the file the claim was first noticed in*, in the report rather than in the code.

### Minor 2 — the `_files_under` enumeration was scoped to one file

Same report section: *"Grepped `tests/test_cli.py` for `_files_under(`."* The claim being made is
that **every** caller was run. **Verified by running** the repo-wide sweep (above): the enumeration
is in fact complete — 8 call sites, 8 functions, none outside `test_cli.py`. No coverage was lost;
the evidence offered just did not rule out a ninth caller elsewhere in `tests/`.

### Minor 3 — Fixture C's docstring under-counts its own claim assertions

`tests/test_cli.py:16052`: *"Two assertions, neither alone sufficient: byte equality … and a
parsed-mapping equality …"*. The test makes **three** claim assertions, not two — line 16107 (bytes),
line 16108 (mapping), and line 16111, `assert repo_root_txt == f"{root.resolve()}\n"`, which pins the
second artifact's exact content including its trailing newline and is covered by neither of the two
the docstring names. A reader who greps this docstring for what the fixture pins will not learn that
`repo_root.txt`'s format is pinned here — and it is pinned **only** here, since the acceptance arm
`.strip()`s it. CLAUDE.md's *count phrases* rule. **On the remedy:** CLAUDE.md prefers deleting a claim to
rewriting it, and that is the default here too — but this docstring's job is to tell a grepper what
the fixture pins, and deleting the count leaves the third assertion undescribed and still
uniquely-pinning. So: name the third and correct the count to three, and do it *for that reason*
rather than as a general licence to rewrite.

### Minor 4 — "Concerns: None found" sits above two mis-scoped claims

The report's closing section states no concerns while §*What I grepped* contains the two grep-scope
overstatements above. The report does correctly refuse the broader zero-disagreements claim
(*"Did not grep for or claim zero disagreements elsewhere in the suite"*), which is the right shape
and is why this is a Minor rather than the ledger's recurring Major.

## Prose checks

**Read.** The `cli.py:2346-2349` comment is exactly two sentences: what the artifacts are for, and
what they are not. It makes **no** claim that a future command reads them (`resume` is not named as a
reader), **no** safety claim substituting for measurement, **no** `E-` code or § Errors row claim, no
count, no positional locator, no `x`-for-`×`, no config-count claim, and no undated build fact — its
only factual claim, that `run.yaml` embeds the config once at the end, is a present-tense spec
property. The acceptance comment (`tests/test_acceptance.py:86-89`) cites "H8b Decision 7" by name.
Fixture C's leading comment cites `docs/superpowers/plans/2026-08-20-diff-freeze.md` § Corrections —
tracked, and the shorthand matches nine existing in-file citations of the same heading — and names
`test_an_unwritable_output_dir_is_a_diagnostic_not_a_traceback` as its precedent, which **verified by
reading** at `tests/test_cli.py:316` is genuinely an inline scaffold-and-run and genuinely above it.

## Gates — all run directly in this worktree

- `uv run ruff check .` → All checks passed.
- `uv run ruff format --check .` → 84 files already formatted.
- `uv run mypy` → Success: no issues found in **47** source files.
- `uv run pytest` → **2542 passed, 1 skipped, 2 xfailed** (twice: once before any mutation, once
  after every revert). Matches the expected count exactly. `pytest-of-joon` and `__pycache__` were
  cleared before both runs.

## What I could not check

- **Nothing about `freeze` itself.** `freeze` is still in `NOT_BUILT_COMMANDS`, so whether these two
  artifacts are *sufficient* for it is not testable at this commit — only that they are what
  Decision 7 specified.
- **`draft`/`resume` writing the pair** cannot be verified by running, because neither command
  exists; I verified only that neither has a second `environment/` write site to have missed.
- **The report's own transcript** (the exact pytest invocations and the `diff -u` against a pre-edit
  copy) was not re-run as written; I reproduced every claim it makes by independent mutation instead.

The tree is clean, stated precisely rather than as an empty `porcelain`: **no source or test file
differs from `6335c1d`** (`git diff` empty, and each mutated file additionally `diff`ed byte-for-byte
against a copy kept before mutating), **no mutation survives** — confirmed by behaviour, by the
post-revert full-suite run at 2542/1/2, never by `git status` — and the temporary worktree at
`c834cd1` was removed (`git worktree list` shows only this one). The **only** untracked path is this
review file itself. `.superpowers/sdd/.gitignore` was checked and is **intact** (its warning header
and the three `task-*-brief.md` / `*.diff` / `*.txt` rules are present, not a bare `*`), so this
file is untracked because it is new rather than because it is ignored — but the previous batches'
reviews are tracked, so commit this one with `git add -f` per CLAUDE.md.
