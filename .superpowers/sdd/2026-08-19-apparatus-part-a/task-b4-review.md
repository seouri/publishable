# H7d Part A batch 4 review — tasks 11, 12, 13

Reviewed at `ec16254` on branch `h7d-apparatus-part-a`. Range under review: `1c0abb0..HEAD`
(`src/publishable/apparatus.py`, `src/publishable/cli.py`, `tests/test_cli.py`, and the batch report).

## Verdicts

- **Spec compliance: PASS.** Decisions 7, 8 and 10 are honoured as written, each verified by running
  rather than by reading. No document was touched, and none needed to be: § The apparatus core can
  only observe already carries the five-key fenced block and the "over the resolved condition →
  facts mapping" wording, so both tasks' "check and change nothing if it agrees" resolved correctly.
- **Task quality: PASS WITH FINDINGS.** One Major and five Minor, every one a prose/claim defect and
  every one fixed by deletion. No finding changes behaviour; the shipped code is correct.

## What the guard pin did, since it was this batch's most important artifact

**Nothing changed in it, and nothing needed to.** Across `1c0abb0..HEAD` `tests/test_cli.py` has
**zero deleted lines**, and production has exactly **one** deleted line — `"apparatus": None,`, the
false null task 11 exists to remove. The pin's body is **byte-identical** to its capture at
`7568a34` (diffed the two extracted function bodies). It stayed green because template `generic`
declares no probe, which is the state the pin was built to hold, so tasks 11 and 12 did not in fact
replace what it covers — they added a second state beside it.

It still discriminates, **verified by running** the exact spelling Decision 7 rejects: with
`cli.py:3530` mutated to `... else {"probe": None}`, the pin fails on
`assert run["provenance"]["apparatus"] is None` → `AssertionError: assert {'probe': None} is None`.
Reverted by editing back and confirmed byte-identical against a pre-mutation copy.

## Verified by running

- **Decision 7, all three shapes.** (a) No probe declared → `provenance.apparatus` is the whole
  block `null`, no `apparatus/` directory (the guard pin, re-run green). (b) A probe returning
  `Apparatus(facts={})` under a template declaring no `apparatus_facts` → the five sub-keys with
  `facts: {"00": {}}` and `unobserved: {}` — Decision 7's third row exactly, raw YAML inspected.
  (c) A probe raising → no `run.yaml`, redacted diagnostic, non-zero exit
  (`test_a_probe_that_raises_is_a_redacted_diagnostic_at_run`, re-run green). No new convention was
  minted: `grep -rn '"probe": None' src/ tests/` returns nothing.
- **Decision 10, not a fourth hash.** `src/publishable/hashes.py` is untouched by the whole slice
  (`git diff main...HEAD -- src/publishable/hashes.py` is empty), `HASHED_TREES` is still
  `("src", "templates")`, and `apparatus_hash` lives at `apparatus.py:485` beside `Observer.block()`.
  Two mutations, both caught by `test_the_apparatus_hash_is_recomputable_from_the_recorded_facts`:
  `sort_keys=False` (**non-blind** — the fixture inserts `zeta_field` before `alpha_field`, so the
  two encodings genuinely differ) and hashing the whole block instead of `facts` alone. Stability
  and sensitivity are pinned by `test_two_runs_..._share_a_hash_and_one_changed_fact_moves_it`.
- **Decision 8's caller, all four properties.** One `W-APPARATUS-UNANSWERED` round at run end, from
  the counts: three findings for six probe calls. **Fresh `Collector`** — the second render prints
  `3 problems (0 errors, 3 warnings)`, not four, so the earlier `W-ENV-UNLOCKED` finding is not
  re-printed. **stdout only** — captured stderr is empty. **Exit code untouched** — the run returns
  `EXIT_OK`, which `run_a_project` asserts.
- **Task 11's and 12's prescribed mutations, reproduced independently.** The `{"probe": None}` block
  (pin fails), `unobserved` built over every returned fact rather than the declared ones
  (`test_the_undeclared_fact_is_recorded_and_has_no_unobserved_entry` fails), `sort_keys=False`, and
  whole-block hashing. All four discriminated; all reverted by editing back.
- **The recorded ledger path resolves.** `(run_dir / block["ledger"]).is_file()` holds in a real run.
- **Gates.** `uv run pytest` → **2417 passed, 1 skipped, 2 xfailed**; `ruff check`, `ruff format
  --check` (82 files), `mypy` (46 source files) all clean. Per-task deltas match the report:
  `e833070`/`e36b5b3`/`c8ecd83` add 3/3/1 new `def test_` against a 2410 baseline.

## The task 11/12 split — adjudicated

Reasonable and correctly disclosed. `e36b5b3` (task 12) is **tests only**, `e833070` (task 11)
carries `apparatus_hash`, because `Observer.block()` cannot emit a `hash` key without it. Task 12's
tests do **pin task 11's code** rather than restate it: two of the three are caught by the two
mutations above, and the recomputation test canonicalizes the mapping it read out of `run.yaml`
rather than asserting a digest literal. Nothing fell between the two — placement, signature,
encoder arguments and the document-versus-file-bytes warning all landed as task 12's brief specifies.

## Findings

### Major

**1. `tests/test_cli.py:13821` — a docstring claim that is false against the code, carried verbatim
from brief prose.** `test_the_undeclared_fact_is_recorded_and_has_no_unobserved_entry` opens
"Decision 4's fourth row, **which no other test reaches**." Three tests already reach it:
`tests/test_apparatus.py:193` (`check_facts` keeps an undeclared fact, task 5),
`tests/test_apparatus.py:373` (an undeclared fact gets no `unobserved` entry, task 7) and
`tests/test_apparatus.py:463` (an undeclared fact reaches the ledger). *Verified by reading those
three test bodies and by `git log -S` dating each to task 5 or task 7 — both landed before this
batch.* What this test uniquely reaches is the fourth row **end to end through
`provenance.apparatus`**, which is worth having; the exclusivity clause is not. It also falsifies the
report's headline — "No other brief, the design, or the plan disagreed with the code encountered
during this batch" — which is the batch-1 failure attack 4 was aimed at, repeated. **Fix by deleting
the clause**, and correct the report's zero-disagreement sentence.

### Minor

**2. `tests/test_cli.py:13998` — a test whose NAME claims a guarantee its body cannot witness.**
`test_the_hash_does_not_cover_unobserved_or_the_probe_name` asserts only that two equal mappings hash
equally and that the digest is `sha256:`-prefixed. *Verified by running:* under the whole-block-hash
mutation this test stayed **green** while only the recomputation test failed. The guarantee is
genuinely pinned — by `test_the_apparatus_hash_is_recomputable_from_the_recorded_facts` — so this is
a claim defect, not a coverage hole. Either name it for what it asserts, or add the assertion the
name promises.

**3. `src/publishable/apparatus.py:497-498` — "`hashes.py`, which holds hashes over the three identity
trees" is wrong three ways and contradicts the precedent the same docstring cites.** `hashes.py`
holds `code_hash`, `parameters_hash` and `design_digest` (*verified by reading its defs*);
`design_digest` is explicitly **not** an identity claim (`reference.md` § What `auto` derives from:
"deliberately not a fourth hash… The digest claims nothing"); `input_manifest_hash` lives in
`manifest.py`, not there; and only `code_hash` is over trees. `allocation_hash`'s own docstring
(`artifacts.py:335`) enumerates the same three correctly. **Fix by deletion** — the sentence ends
sound at "and not in `hashes.py`."

**4. `tests/test_cli.py:14037` — task 13's docstring says the credential sweep is "sliced out of
`run.yaml`"; the body sweeps the whole file text** (`assert _ORDINARY_CRED_VALUE not in
run_yaml_text`). Stronger than claimed, so no coverage gap — but a second brief-prose claim the body
does not implement, and a leak anywhere else in `run.yaml` would fail a test named for the apparatus
block. Fix the sentence or slice the text.

**5. `tests/test_cli.py:13789` — `x` where the house style is `×`.** `"run_start (2) +
pre_execution (4, two conditions x two repeats)"`, inconsistent with the same batch's own fixture
comment and report, both of which write `×`.

**6. Three new positional "above" qualifiers in shipped source** (`apparatus.py:504` "the exact
`json.dumps` arguments above"; `cli.py:3585` "print to stdout above"; `cli.py:3588`
"`W-ENV-UNLOCKED`'s own precedent above"). Each names its referent, so all three survive a grep and
none is a bare locator — but the positional word is the part an insertion falsifies, and it buys
nothing the name does not already give. Fold into one deletion pass.

**7. Nothing joins the recorded ledger path to the file it names.** `apparatus.py:357`
(`ledger_dir / "probes.jsonl"`) and `apparatus.py:478` (`"ledger": "apparatus/probes.jsonl"`) are
independent spellings; the only assertion (`tests/test_cli.py:13783`) compares the recorded string to
its own literal, and every ledger-reading test hard-codes the path rather than following the record.
*Verified by running that the join holds today* — `(run_dir / block["ledger"]).is_file()` — so this
is an unpinned property, not a defect. One line in the existing task 11 test closes it.

## Could not check

- **The block's contents on a `partial` or `failed` run.** Decision 7's table does not cover it, and
  Part B owns `status: partial` for the raise path, so there is no ruling to check the code against.
- **A non-finite float fact's effect on canonical-JSON reproducibility** (`json.dumps` emits bare
  `NaN`, which is not JSON). That is Decision 5 / task 5's surface, not this batch's.
- **The ledger line for the task 11/12 split.** The deviation is disclosed in the report and is a
  ruling, so it is owed a `progress.md` entry — the post-review ledger commit's job, not a finding
  against the implementer.

## Tree state

Clean. Every mutation was reverted by editing back and re-verified by behaviour (re-running the
affected test) and by `diff` against a pre-mutation copy; the temporary probe test used for the
Decision 7 and Decision 8 shape checks was deleted. Full suite, all three gates and `git status`
re-run after the deletion: 2417 passed, gates clean, working tree clean apart from this review file.
