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

No other brief, the design, or the plan disagreed with the code encountered
during this batch. `reference.md` § The apparatus core can only observe
already carried the exact five-key fenced example and the `hash` semantics —
nothing there needed changing, matching both task 11's and task 12's "check
and change nothing if it agrees" instruction.

## warn_unanswered's caller

Wired in this batch, at task 11, as instructed: `command_run` calls
`observer.warn_unanswered(warn_c)` once, at run end, through a fresh
`Collector`, printed to stdout only when non-empty.

## Concerns

None outstanding. All three tasks' prescribed mutations discriminated as
described; none was caught only by a crash or a string literal.
