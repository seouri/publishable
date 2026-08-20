# Batch 5 review — tasks 6, 7 (the upstream ledger and `provenance.upstream`)

Reviewed 2026-08-20 on branch `h8a-lineage` at `eedcfbf`, covering commits `ea8174e` (task 6),
`d6e65ed` (task 7) and their two record commits. Tree left clean.

## Verdicts

- **Spec compliance: PASS.** Decision 6 (all four steps), Decision 7 and Decision 8's four-key
  entry are built as written; the one authorized pin edit was made by the named task, in both
  places the list is pinned, as exactly one appended key with nothing reordered and no assertion
  weakened.
- **Task quality: PASS.** **All nine mutations the two briefs prescribe were re-run here and every
  one failed**; eight failed at the assertion the brief credits, and one (the run-stop widening) is
  caught earlier than the brief's own account — see § 5. Three Minors, all prose/docstring.

## Gates (run here, at `eedcfbf`, unfiltered and in the foreground)

`uv run pytest -q` → **2510 passed, 1 skipped, 2 xfailed** (137.4 s) — matches the report.
`ruff check .` → All checks passed. `ruff format --check .` → 84 files. `mypy` → 47 source files.
Re-run after every mutation was reverted: identical. `git status --short` empty, `git diff --stat`
empty.

## 1. The authorized pin edit — verified, honoured exactly

**Verified by diffing, not by the report's transcription.** `git show d6e65ed -- tests/test_cli.py`
has exactly **one** deleted assertion line in the whole file — `assert "upstream" not in
provenance` — replaced by `assert provenance["upstream"] == []`, which is strictly stronger (the
old `not in` was already implied by the exact-list assertion). Both key lists
(`tests/test_cli.py:12906`, `list(run["provenance"]) == [...]`, the shipped H7d test; and
`tests/test_cli.py:15364`, `list(provenance.keys()) == [...]`, arm B) gained one line, `"upstream",`
after `"allocation_hash"`. **No reorder, no subset check, no `sorted()`, no set, no membership
substitution.** The H7d test's existing docstring paragraphs — including the argument for asserting
the whole list — appear as **context** lines, unchanged, with a new paragraph appended: the
"editing the assertion *and* the argument for it" hazard `CLAUDE.md` names for this exact test did
not occur. Arm A and arm C are untouched (no `-` lines anywhere near them).

**Both still discriminate — verified by running.** Inserted a junk key
(`"spurious_review_key": 1`) into `command_run`'s provenance dict at `src/publishable/cli.py:3671`:
both tests failed, `test_a_run_with_no_declared_probe_records_a_null_apparatus_block_and_no_ledger`
and `test_h8a_arm_b_the_provenance_key_list_and_upstream_empty`, the latter at
`tests/test_cli.py:15364` with *"Left contains one more item: 'spurious_review_key'"*. Mutation
reverted by editing back; `diff` against a pre-mutation copy → identical.

**These are the only two pins of that list, and the suite proves it rather than my grep patterns.**
A green 2510 at HEAD is the proof: any unedited pin of the old twelve-key list would fail now that
the key is written. (The grep over `tests/*.py` for `"allocation_hash",` and
`list(provenance`/`list(run["provenance"])` agrees — two sites, both edited.)

## 2. Decision 7 — `[]` always, inserted after `allocation_hash`

**Verified by running all three shapes** through a throwaway probe (`tests/`-local, deleted after;
it read the *raw* `run.yaml` text with a regex over the `provenance:` block rather than trusting
`yaml.safe_load` key order):

| Shape | `provenance` key order | `upstream` |
|---|---|---|
| Real run, no `reuse_from` anywhere | 13 keys, `upstream` last, immediately after `allocation_hash` | `[]` |
| Real run reading a second real run's `shared/<step>/out.json` | same order | one entry, exactly `run_id`, `code_hash`, `parameters_hash`, `used` |
| Real run whose `reuse_from` raised `E-UPSTREAM-ARTIFACT-MISSING` | same order | `[]` |

Present and correctly shaped in all three; `[]` rather than `None` or absent in both no-entry
shapes, which is Decision 7. Position matches `reference.md` § The two files (`upstream` after
`allocation_hash`); its appearing *after* `publishable_version`/`plugin_versions` is the
pre-existing cosmetic divergence `spec-defects.md` already records, not new.

**Every site that could write this key was enumerated, since the two pins only see `command_run`.**
`grep` over `src/publishable/*.py` for `assemble_run_yaml`, `provenance:` construction and
`run.yaml` writes: **one** provenance dict (`cli.py:3616`), **one** `assemble_run_yaml` call
(`cli.py:3673`), **one** `run.yaml` write (`cli.py:3688`), and the only commands that exist are
`command_validate` and `command_run` (`draft`/`resume` are unbuilt). So "always a list" has no
second surface that could diverge. Verified by reading + grep.

## 3. Task 6's three claims — each verified independently by running

**The sort is observable, and the container is deterministic.**
- Fixture O's read order is genuinely non-sorted by construction (`c.json`, `a.json`, `b.json` for
  `used`; `bbb`, `aaa`, `ccc` for entries) — read from the fixture source, and all three candidate
  orderings differ as the design's table claims.
- Deleting the `sorted()` on `used` (`"used": list(entry["used"])`) → **FAILED** at
  `tests/test_lineage.py:742`, the exact-list assertion. Run under `PYTHONHASHSEED=0`, `1` and
  `12345` in three separate processes: **failed all three**, same line. The container is a plain
  `dict` (insertion-ordered) of plain `list`s, so the pin is deterministic by construction, not by
  luck — the report's set → list fix is the right one and it is what makes this mutation a sort pin.
- Deleting the `sorted()` on entries → **FAILED** at `tests/test_lineage.py:762`.

**Entry kept across a failing execution.** Added `upstream.ledger._entries.clear()` to
`runner.py`'s per-execution `except Exception` → **FAILED** at `tests/test_cli.py:15519`
(`assert len(entries) == 1`), the prescribed assertion.

**The retargeted raise-site mutation fails at the exact site.** Moved
`self._upstream.ledger.record(...)` to *before* the `target.exists()` check in
`artifacts.py:reuse_from` → **FAILED** at `tests/test_cli.py:15561`,
`assert record["provenance"]["upstream"] == []`, with the mutant's entry naming
`step02_publish/not_there.json` — an artifact that does not exist, which is exactly the
unverifiable-chain state Decision 6 step 1 exists to prevent. The report's account of why the first
attempt was blind is confirmed by reading: an `E-UPSTREAM-STEP-UNKNOWN` raise happens inside
`locate_step`, two statements above the moved line, so it cannot distinguish the branches.

**Key-by-locator mutation.** Re-keyed `setdefault` on `f"{step}|{name}"` (any key other than
`run_id`) → **FAILED**, `assert len(entries) == 1` → `assert 2 == 1`, in
`test_fixture_o_both_locator_forms_for_one_upstream_merge_into_one_entry`.

## 4. The ledger's key — the split is right

Two locators addressing one run must produce **one** ledger entry, and the code agrees: verified by
running a direct-call probe (relative locator, then absolute locator, then the relative one again,
three reads of one upstream) → **one** entry, `used == ["step01/x.json", "step01/y.json"]`. That is
what `reference.md` § `reuse_from` requires — *"`provenance.upstream` records the resolved `run_id`
and never the path"* — and Decision 6's *one answer per run*. The resolver's locator keying (batch
3's `AAAA`/`BBBB` Major) answers a different question — the same locator asked twice cannot get two
answers — and keying the ledger the same way would have produced two entries for one ancestor.
**Judged correct, and correctly separated in both docstrings.**

## 5. The remaining four prescribed mutations — also re-run here

**Task 6's run-stop widening — caught, but not by the assertions the brief credits.** Added
`if str(getattr(exc, "code", "") or "").startswith("E-UPSTREAM"): raise` at the top of
`runner.py`'s per-execution `except Exception` → **FAILED**, but at
`tests/test_cli.py:248` — `run_a_project`'s own `assert main(["run", …]) == expect_exit`, `1 != 4`
— so `run.yaml` never exists and the *"`run.yaml` exists"* and *"second ledger line"* assertions the
brief names are never reached. **The mutant is caught deterministically; the credited assertions are
not what catch it.** Worth carrying, because this is the mutation the brief singles out as *"the
mutation for the claim no comment may make"*: the property actually pinned is *the exit code stays
`EXIT_FAILED`*, and the two record-survival assertions are exercised (unmutated) by Fixture F's
`ValueError` half, which a code-agnostic widening would also break at the same exit assertion. Not
a finding — the report disclosed the same mechanism — but a reviewer of a later slice should not
read those two assertions as the run-stop pin.

**Task 7's three, all three failing as the brief prescribes.**
- *Write `upstream` only when non-empty* (removed the dict key; re-added conditionally before
  `assemble_run_yaml`) → **three tests failed at once**: Fixture E at `tests/test_cli.py:15581`,
  the **membership** assertion (`assert "upstream" in provenance`) — the one that names the fault —
  plus arm B and the shipped H7d test. This is the discriminating direction the spurious-key
  mutation cannot see: it proves the pins catch a *missing* key, not only an added one, which is the
  whole content of Decision 7. Fixture R correctly stayed green.
- *Copy the downstream's hashes* (hard-coded a placeholder in `record`) → **FAILED** at Fixture R's
  read-back comparison, `entry["code_hash"] == upstream_record["code_hash"]`. The fixture's own
  "the two runs' trees differ" pre-assertion is what makes this arm non-vacuous, and it holds.
- *Add a fifth key* (`"note": "extra"` in `entries()`) → **FAILED** at Fixture R's exact-key-list
  assertion, *"Left contains one more item: 'note'"*.

All nine mutations reverted by editing back (never `git checkout --`); all four touched source files
(`cli.py`, `lineage.py`, `artifacts.py`, `runner.py`) byte-compared against pre-mutation copies and
identical, then a final unfiltered suite re-run green at 2510 with all three gates clean.

## Findings

### Minor 1 — `UpstreamLedger.record`'s docstring claims a guarantee the code does not provide
**File:** `src/publishable/lineage.py:284-289` (the `record` docstring).
It reads: *"`code_hash` and `parameters_hash` are copied from `record` the first time this `run_id`
is seen and never re-read afterward, **which is what makes N reads from one upstream do one record
read**"*. **Verified by running**: instrumented `lineage.read_run_record` with a counter and did
three `reuse_from` calls against one upstream through two distinct locators (`run_id`, then the
absolute path, then `run_id` again) → **2 record reads**, not one. The ledger performs no I/O at
all; the only cache that avoids a read is `UpstreamResolver._records`, keyed by the locator string,
so two locators naming one run do two reads today — deliberately, per batch 3's ruling. The
property the ledger *does* provide is the one Decision 6 actually needs (first-sight `setdefault`
→ one answer per run in the record), and the report itself concedes the brief was "loose about
which object does the caching" — but the shipped docstring carries the claim anyway, which is the
named repo habit (*a comment claiming a guarantee the code does not provide*). **Prefer deleting the
false half** ("which is what makes N reads … one record read") over rewriting it; the parenthetical
that follows already attributes caching to the resolver correctly.

### Minor 2 — `record.get("code_hash")` publishes `code_hash: null` into the chain for a record `read_run_record` would otherwise call "edited or truncated"
**File:** `src/publishable/lineage.py:296-297`.
`record.get("code_hash")` / `.get("parameters_hash")` fail open: **verified by running** — the
synthesized-upstream probe produced an entry `{'run_id': …, 'code_hash': None, 'parameters_hash':
None, 'used': [...]}`. `read_run_record` validates `run_id` and `schema_version` and nothing else,
so a record declaring this build's `schema_version` while missing a hash is exactly the hand-edited
case that already has a code (`E-UPSTREAM-RECORD-UNREADABLE`, *"edited or truncated"*), and
Decision 8's obligation is *"that the four keys are true"*. No fixture covers it (Fixture O's
synthesized upstreams never assert the hashes; only Fixture R does, against a real run). Not a
behaviour change to make inside this batch — **a filing with an owner is the proportionate
disposition**, since the alternative reading (`null` honestly means "the upstream's record did not
carry one") is defensible and belongs to whoever owns chain verification (H8b/H9).

### Minor 3 — two positional locators in the new `spec-defects.md` amendment, one of them ambiguous
**File:** `docs/superpowers/spec-defects.md:3280` and `:3306-3308`.
The struck row says *"see the amendment below"* — but that section now holds **two** amendments,
and the first one below the table is the 2026-08-13 H3c1 amendment whose own last sentence says
`provenance.upstream` *"is unaffected and still unwritten"*. A reader following "below" lands on the
paragraph that contradicts the strike. And the new amendment ends with *"The 'deliberately not
fixed' key-order note **two paragraphs above**"* — it does name what the note does, so it is
half-compliant, but the positional half goes stale on the next insertion, which is the trap
`CLAUDE.md` counts seven instances of. Fix by naming the target (*"see the 2026-08-20 amendment
below"*, and *"the 'deliberately not fixed' key-order note"* with no position). The 2026-08-13
amendment's now-stale sentence is **not** a finding: it is dated, and the new amendment supersedes
it in the same file.

## Sequencing claim (Fixture F committed with task 7) — verified by running, not only by reading

Two independent checks:
1. **By reading the commit's file set:** `git show ea8174e --stat` touches only
   `src/publishable/artifacts.py`, `src/publishable/lineage.py`, `tests/test_lineage.py` — neither
   `cli.py` nor `tests/test_cli.py`. `git grep '\.entries' ea8174e -- src tests` returns only the
   three Fixture O call sites, so task 6's `entries` attribute → method rename had no other
   consumer and no test at that commit asserts `provenance.upstream`.
2. **By running:** cloned the repo (`git clone --no-hardlinks` into the scratchpad, not a worktree
   in this tree), checked out `ea8174e`, ran `uv run pytest -q` there →
   **2506 passed, 1 skipped, 2 xfailed**, exactly the figure the report claims (+3 for Fixture O).
   Clone deleted afterwards. The report's stash-based verification is corroborated independently.

The reasoning for the placement is sound: Fixture F asserts `provenance.upstream` through a real
`run`, the key does not exist until task 7's `cli.py` edit, and the alternative (reaching into
`StepIO._upstream.ledger` from a `run`-level test) is the direct-call shortcut H7d Part A's only
Critical proved blind.

## Prose

Checked and clean: no § Errors row is touched (task 9's); every citation is to a **tracked**
`docs/superpowers/{specs,plans}/…` file — no `task-*-brief.md` (git-ignored) is cited; no
config-count or executability claim appears anywhere in the batch's diff (swept for
`of nine`/`nine configs`/`executable`/`no remaining core-side` over all added lines → no hits), so
the table row is left for task 10; no multiplication `x`; no trailing whitespace, tab or invisible
unicode in any added line. `reference.md` § Package layout still marks `lineage.py`
*"— not yet built"* — **not a finding**: plan task 9 step 6 owns removing it.

## What I did not check

- Fixture P, the scope arms, and the § Errors/§ Executability rows — tasks 8, 9, 10, batch 6.
- Batches 1–4's rulings (the resolver's locator-keyed cache, Fixture N's arms, `_contained`) were
  treated as closed and not re-litigated.
- The `E-ARTIFACT-UNREADABLE` route through `_read` (a writer-without-reader suffix) is not covered
  by a fixture; I confirmed by reading that `ledger.record` sits after `self._read(target)` on the
  same straight-line path, so no mutation could distinguish it from the covered raise sites.
- Whether a *copied* upstream directory carrying the same `run_id` but different hashes should merge
  into one entry (first-sight wins today). Reachable only by hand-copying a run; the design's *one
  answer per run* reads as intending exactly this, so I raise it as an observation, not a finding.
