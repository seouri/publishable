# H7d Part A batch 4: tasks 11, 12, 13

## Status

All three tasks done, gates clean, suite green at each step.

## Commits

- `e833070` — H7d Part A task 11: provenance.apparatus stops being a false null
- `e36b5b3` — H7d Part A task 12: the apparatus fingerprint, beside its construction and not in hashes.py
- `c8ecd83` — H7d Part A task 13: the recorded block is publishable as-is

## Test summary

Starting point: 2410 passed, 1 skipped, 2 xfailed.

- After task 11 (+3 tests): 2413 passed, 1 skipped, 2 xfailed.
- After task 12 (+3 tests): 2416 passed, 1 skipped, 2 xfailed.
- After task 13 (+1 test): 2417 passed, 1 skipped, 2 xfailed.

Each full, unfiltered `uv run pytest` run matched its brief's stated delta exactly.
Gates run after every task: `uv run ruff check .`, `uv run ruff format --check .`
(via `ruff format .` — no diffs beyond the run's own new tests), `uv run mypy`
(46 source files) — all clean throughout.

## What changed, task by task

**Task 11.** `Observer.block()` (new, in `apparatus.py`) assembles the five
sub-keys — `probe`, `ledger`, `hash`, `facts`, `unobserved` — from
`Observations.facts_document()` and `Observations.unobserved()`, calling
`apparatus_hash` (task 12's function, necessarily written here too — see
"Deviation" below) rather than re-deriving anything. `cli.py`'s
`"apparatus": None,` line became
`"apparatus": observer.block() if observer is not None else None,`, same
position in the dict. `Observer.warn_unanswered` got its call site: once at
run end, inside the `RunLock` block right after `run.yaml` is written, through
a **fresh** `Collector` (never the one already rendered above) carrying
`credentials`, printed to stdout only when it produced findings — `run.yaml`
has no diagnostics channel, on `command_run`'s own stated precedent for
`aggregate_c`'s findings, and a warning never touches the exit code, on
`W-ENV-UNLOCKED`'s existing precedent.

Three tests, Fixture N (two conditions × two seed repeats → six probe calls,
3 per condition): the five-key block with a never-answered fact and an
answered one, both read from `run.yaml` and cross-checked against a value
recomputed from the ledger (never hard-coded); the undeclared-fact
presence/absence pair; the three-line `W-APPARATUS-UNANSWERED` count (the
never-answered pair plus the two partially-answered pairs, none for the
always-answered fact or the undeclared one).

Two mutations, both behaved exactly as prescribed:
- (a) writing the block unconditionally with `probe: None` for no-probe runs
  → task 18's guard pin **FAILED** on `run["provenance"]["apparatus"] is None`.
- (b) building `unobserved` from every returned fact instead of the declared
  ones → the undeclared-fact test **FAILED** (`extra_diagnostic` gained an
  `unobserved` entry the test asserts is absent).

Both reverted by editing back and reconfirmed green.

**Task 12.** `apparatus_hash(facts_document) -> str` in `apparatus.py`,
beside `Observer`/`Observations` rather than in `hashes.py` — sha256 over
canonical JSON (`sort_keys=True`, `separators=(",", ":")`,
`ensure_ascii=False`) of the facts mapping alone, `sha256:`-prefixed.
`HASHED_TREES` untouched. This was already written as part of task 11's
commit, since `Observer.block()` cannot produce a `hash` key without it —
see "Deviation" below.

Three tests, none asserting a digest literal: recomputed-from-`run.yaml`
(Fixture H, with two facts inserted in *reverse* sorted order —
`zeta_field` before `alpha_field` — so the `sort_keys` mutation below is not
blind); two independent runs with identical facts share a hash despite
different run directories, and a run with one changed fact value gets a
different hash; a direct call proving the function's signature covers facts
alone (two dicts differing in nothing but construction hash identically,
and `apparatus_hash` takes no `probe_name`/`unobserved` parameter at all to
diverge on).

Two mutations:
- Hash the whole block (`probe`, `ledger`, `facts`, `unobserved`) instead of
  `facts` alone → the recomputation test **FAILED** (digest mismatch).
- `sort_keys=False` → the recomputation test **FAILED** (digest mismatch;
  confirmed non-blind precisely because the fixture's insertion order
  differs from sorted order, as the brief requires checking).

Both reverted and reconfirmed green.

**Task 13.** One test, `test_the_recorded_apparatus_block_carries_no_credential_value`:
a run whose template declares `required_env = ["PUBLISHABLE_TEST_TOKEN"]`
and whose probe returns ordinary facts (never reading the credential) is run
to completion; the block is asserted non-null and populated (ruling out a
vacuous absence-sweep pass), and the credential value is asserted absent from
`run.yaml`'s raw text, sliced rather than re-parsed. Docstring states
explicitly what this does not prove (the ledger's or the terminal's
property — Fixture K and K2, task 9, cover those).

Mutation: in `check_facts`, redact a credential-equal value into `facts`
instead of raising `E-APPARATUS-FACT-CREDENTIAL`. Run together with task 9's
Fixture K test as instructed:
- Task 13's own test: **PASSED** (vacuously — its probe never returns the
  credential, so the mutated branch is never reached).
- Fixture K test (`test_a_probe_returning_a_declared_credential_fails_the_command_and_writes_no_run_yaml`):
  **FAILED** — exit code became `0` instead of `EXIT_WRONG`, and `run.yaml`
  was written where the test asserts none exists.

Reverted and both tests reconfirmed green together.

## Deviation from the batch's task split, reported rather than silently done

`apparatus_hash` (task 12's own deliverable) had to be **written** during
task 11, because `Observer.block()` cannot assemble a `hash` sub-key without
it — the brief's own step 1 for task 11 says "assembling from `Observations`
... and wire it in `cli.py`," which is impossible without the hash function
existing first. Task 12's commit therefore adds **only its tests**; the
production code landed one commit earlier than its own task number. Placement,
signature, and docstring all follow task 12's brief exactly (beside the
builder, not in `hashes.py`, sha256 over canonical JSON of facts alone).

**Corrected in fix round 1 — this batch's report originally claimed zero
brief/code disagreements. That was false.** Two are named below in full; see
Fix round 1 for how each was found and closed.

1. Task 11's own test docstring (`test_the_undeclared_fact_is_recorded_and_has_no_unobserved_entry`)
   claimed it reached "Decision 4's fourth row, which no other test reaches."
   Three tests already reach that row — `tests/test_apparatus.py:193`, `:373`
   and `:463`, dated by `git log -S` to tasks 5 and 7, both landed before this
   batch. The clause was carried verbatim from this report's own drafting
   rather than checked against the code with a grep, which is exactly the
   kind of claim this project's own `CLAUDE.md` § Habits that cost real work
   warns against ("sweep for the claim, not for the file it was first noticed
   in") — here it was a claim never swept for at all.
2. Task 13's test docstring claimed its credential sweep was "sliced out of
   `run.yaml`," while the test body sweeps the whole file's raw text. The
   divergence is in the harmless direction (the implemented check is
   strictly stronger than the one described), but it is a second instance of
   the same failure mode: brief-style prose about what the code does,
   asserted without checking it against the body of the test it describes.

`reference.md` § The apparatus core can only observe itself needed no change
— it already carried the exact five-key fenced example and the `hash`
semantics, matching both task 11's and task 12's "check and change nothing if
it agrees" instruction. The two disagreements above are both in this batch's
*own test prose*, not between the code and the four documents.

## warn_unanswered's caller

Wired in this batch, at task 11, as instructed: `command_run` calls
`observer.warn_unanswered(warn_c)` once, at run end, through a fresh
`Collector`, printed to stdout only when non-empty.

## Concerns

None outstanding. All three tasks' prescribed mutations discriminated as
described; none was caught only by a crash or a string literal.

## Fix round 1

Review at `.superpowers/sdd/2026-08-19-apparatus-part-a/task-b4-review.md`,
reviewed at `ec16254`. Spec compliance PASS; task quality PASS with findings —
one Major, six Minor, every one a prose/claim defect, none changing behaviour.
Commit: `e636f15`.

**Major 1 — the false "no other test reaches" claim, and the corrected
disagreement count.** Deleted the clause from
`test_the_undeclared_fact_is_recorded_and_has_no_unobserved_entry`'s docstring
rather than rewriting it, per house style. *Verified by*: `grep -rn "no other
test reaches" tests/` now returns nothing, and the corrected report above
names both disagreements this batch actually found, with `git log -S` dates
for the three tests that already reach Decision 4's fourth row
(`tests/test_apparatus.py:193`, `:373`, `:463`).

**Minor 2 — the test name claiming a guarantee its body cannot witness.**
Renamed `test_the_hash_does_not_cover_unobserved_or_the_probe_name` to
`test_apparatus_hash_s_signature_admits_only_a_facts_mapping`, which is the
narrower, accurate claim the body actually makes (the function's signature
takes no `probe_name`/`unobserved` argument to diverge on). *Verified by*:
re-ran it under the whole-block-hash mutation from task 12's own step 4 —
still green, exactly as the review found, because the renamed claim is a
signature-level fact this mutation cannot touch; the broader guarantee stays
pinned by `test_the_apparatus_hash_is_recomputable_from_the_recorded_facts`,
which fails under that same mutation.

**Minor 3 — `apparatus.py`'s false gloss on `hashes.py`.** Deleted "which
holds hashes over the three identity trees" — `hashes.py` holds `code_hash`,
`parameters_hash` and `design_digest` (the last explicitly not an identity
claim per `reference.md` § What `auto` derives from), `input_manifest_hash`
lives in `manifest.py`, and only `code_hash` is over trees. The placement
argument stands without the gloss: "beside the builder... and not in
`hashes.py`." Also deleted the sibling "above" locator two paragraphs later
("the exact `json.dumps` arguments above") in the same pass, replacing it
with "this function uses" (folds into Minor 6, same file).

**Minor 4 — task 13's "sliced out of `run.yaml`" claim.** The body always
swept the whole file's raw text, which is stronger, not weaker, than
described. Rewrote the docstring to say so plainly rather than narrow the
check to match the false claim. *Verified by*: re-ran
`test_the_recorded_apparatus_block_carries_no_credential_value` — still
passes, the actual assertion is unchanged, only the words describing it
moved to match what they describe.

**Minor 5 — `x` for `×`.** Fixed the one instance the review named
(`tests/test_cli.py`'s ledger-count assertion message,
"two conditions x two repeats" → "two conditions × two repeats"); confirmed
no sibling instance in this batch's new code via a targeted grep.

**Minor 6 — the three new "above" locators.** Removed all three: `cli.py`'s
warn-site comment ("stdout above" → "stdout"; "precedent above" → "precedent")
and `apparatus.py`'s docstring (folded into Minor 3's edit above). Each named
its referent already, so none was broken — this was a house-style cleanup,
not a correctness fix.

**Minor 7 — the ledger path join was asserted but never proven to resolve.**
Added `assert (doc["run_dir"] / block["ledger"]).is_file()` immediately after
`test_a_declared_probe_records_the_five_sub_keys_per_condition`'s existing
`block["ledger"] == "apparatus/probes.jsonl"` literal check, joining the
recorded string to the file it names rather than comparing two independent
spellings to each other. *Verified by running*: passes today (the review's
own finding that this was unpinned-not-broken), and the test still passes
after the addition.

**Gates and full suite, re-run after all seven fixes**: `uv run pytest` →
**2417 passed, 1 skipped, 2 xfailed** (unchanged — no test was added or
removed, only renamed and corrected). `ruff check`, `ruff format --check`
(82 files), `mypy` (46 source files) all clean.

**Lesson, stated as asked**: a brief's prose about other tests — or about
what a test's own body does — is a claim about the code, and it is checkable
by `grep` before it is written down. This round's Major and its Minor 4
sibling were both exactly that: prose carried forward and never swept for.
