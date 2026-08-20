# H8a — whole-branch review (`h8a-lineage` → `main`)

**Verdict: MERGE.** One Major was found and **closed in this review** (a normative document repair,
no code change, `docs/reference.md` only — see the fix commit below this one); four Minors remain, each
cheap and none blocking.

Reviewed at `2065682`, 12 tasks / six batches, independently of the six batch reviews. Everything
below is labelled **verified by running** or **read**. Gates at this commit, run by me:

| Gate | Result |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 84 files already formatted |
| `uv run mypy` | no issues, **47 source files** |
| `uv run pytest` | **2512 passed, 1 skipped, 2 xfailed** (137s) |

All four match the plan's predicted literals (§ Corrections, correction 7: mypy 46 → 47, formatter
82 → 84).

---

## Findings

### Major 1 (FOUND AND FIXED IN THIS REVIEW) — `E-UPSTREAM-REPO-CONTAINED`'s § Errors row and its § Lineage paragraph were both narrower than the code, and this is a cross-batch interaction

**Where.** `docs/reference.md:1049` (§ Errors core raises) — *"…, or an **absolute path** resolving
inside the git repo the command was given"* — and `docs/reference.md:3175` (§ Lineage between runs)
— *"**The absolute form** is checked against the same containment invariant `output_dir`/`input_dir`
already enforce"*. Neither says the **relative** form is checked.

**What the code does.** `src/publishable/lineage.py` raises `E-UPSTREAM-REPO-CONTAINED` from **two**
sites: line 136 (absolute branch) and **line 151 (relative branch)**. The second was added by task 3
(`569113f`) when it closed the *"`resolve_run`'s relative form skips the repo-containment check"*
filing — the relative branch now resolves its path and runs `resolves_inside_repo` on it.

**Verified by running.** On my own two-run project driven through the real console script
(`uv run publishable run`), with a copy of a real run directory placed inside the project's git repo
at `proj/inrepo_run` and `<output_dir>/inrepo_ln` symlinked to it:

- absolute locator `…/proj/inrepo_run` → `E-UPSTREAM-REPO-CONTAINED` (the documented arm)
- **relative locator `inrepo_ln` → `E-UPSTREAM-REPO-CONTAINED`** (the undocumented arm)

**Why no batch review could see it.** Batch 3 widened the check; batch 6 wrote both document rows
from Decision 1, whose text says the relative form *"inherits the guarantee for free"* and attributes
containment to the absolute form alone. The design is development record and is correctly not
retro-edited — but the **normative** rows were written from it and nobody re-read them against the
shipped two-site code. This is the exact shape `CLAUDE.md` names (*"§ Errors carries one row per code,
not per emit site"* / *"a row narrower than its code is the `E-TEMPLATE-UNKNOWN` two-emit-sites
shape"*) — and the same slice's task 9 repaired precisely that fault for `E-ARTIFACT-NAME` three rows
above. `lineage.py`'s own `resolve_run` docstring **is** complete (lines 116-127 explain the relative
branch's check); only the documents are not.

**Fix, applied here** (the repo's own rule is *the document changes first*, and the behaviour is
already right): the § Errors row now reads *"a locator of **either** form resolving inside the git
repo … the relative form's path is resolved before that check too, so a symlink under `output_dir`
pointing into the repo is refused the same way an absolute path to it is"*, and § Lineage's paragraph
now opens *"**Both** forms are checked …"* and carries the reason the exemption was withdrawn (an
ordinary subdirectory of `output_dir` inherits the guarantee; a symlink under it does not, and core
writes one itself as `latest`). Re-verified after the edit: mechanical pass **0 problems**, suite
**2512 passed, 1 skipped, 2 xfailed**. No code touched.

### Minor 1 — a stated Decision 6 rule is unpinned: moving `ledger.record` above `_read` leaves the whole suite green

**Where.** `src/publishable/artifacts.py:920-923`, the comment on the accumulation line: *"a call
that raised above this line, **or that `_read` itself raises** (an unregistered writer-without-reader
suffix), never reaches this and the ledger stays untouched for it."*

**Verified by running.** One-line mutation — insert
`self._upstream.ledger.record(step=step, name=name, record=record)` immediately **above**
`result = self._read(target)` — and the full suite is **2512 passed, 1 skipped, 2 xfailed**: green,
unchanged. The claim about `_read` is true of the code and pinned by nothing.

Batch 5 did run this mutation (its report, mutation table row 4) but applied it **above the
`target.exists()` check**, which Fixture F's raising half catches through
`E-UPSTREAM-ARTIFACT-MISSING`. Between `exists()` and `_read` there is no fixture at all. The
discriminating one is cheap: an upstream artifact whose suffix has a registered writer and no reader
(the shipped `E-ARTIFACT-UNREADABLE`), or an unparseable `.json` — containment and existence pass,
`_read` raises, and the two branches differ in whether `provenance.upstream` names an artifact that
never came back. That is the precise state Decision 6 step 1 exists to prevent (*"a `used` list
naming an artifact that is not there would make the chain unverifiable"*). **Correct fix, shipped
unpinned** — the failure `CLAUDE.md` records five times in three slices.

### Minor 2 — a review obligation assigned to task 12 was never discharged or dispositioned: `_resolve` still holds its own copy of the containment predicate

**Where.** `src/publishable/artifacts.py:694-701` (`_resolve`) versus `:955-963` (`_contained`). The
two predicates are token-for-token the same test with different messages:

```
if Path(name).is_absolute() or not str(candidate).startswith(str(base) + os.sep):
```

`task-b3-review.md` (§ Task 12's boundary) states: *"the `_resolve` at line 697 still holds its own
copy of the predicate — correct for this batch, and **task 12's to unify**."* Task 12's brief, its
report and its review never mention it (verified by grep over all six reports and reviews plus
`task-12-brief.md`). Two copies of one rule is the drift argument `lineage.py`'s own docstring makes
about importing `SCHEMA_VERSION` rather than restating it. Either unify (`_resolve` becomes
`return self._contained(self.step_dir, name, code="E-ARTIFACT-NAME")`, keeping whichever message is
wanted) or file it with the reason for keeping two.

### Minor 3 — no report names what `CLAUDE.md` owes, which the plan required

Plan task 9 step 6: *"`CLAUDE.md` is a file the controller edits, not this task — the report names
what `CLAUDE.md` owes rather than editing it."* No batch report contains such a statement (verified
by grep; `task-b6-report.md` § Concerns says *"None outstanding"* and raises an unrelated census-table
question). Concretely owed at merge: an **H8a slice entry** — every prior slice has one and the last
is H7d Part B — and the § Order line's `H8` narrowed to `H8b, H8c`. The minting-site correction the
ledger ordered was already made on `main` (`1540b6f`, `28e311d`) and is intact; the § Order line
already reads *"H8, H9, and H3c-3's remaining 14"*. So this is one paragraph, not a sweep.

### Minor 4 — temporal language left in shipped docstrings, one of it stale

- `src/publishable/lineage.py:4` — *"and (from later tasks in this slice) the locator resolution and
  containment machinery"*. That machinery is in the file; *"later tasks in this slice"* means nothing
  to a future reader and reads as if it is absent.
- `src/publishable/lineage.py:46` — *"the named step's own recorded status is **a later task's
  check**, not this one's."* That check ships **in the same module** now (`resolve_step`,
  `E-UPSTREAM-STEP-INCOMPLETE`); name it. This is the *"docstring written in one batch, falsified by a
  later one, never re-read"* shape, in its mild form.
- `src/publishable/lineage.py:351-365` — the cache comment credits locator-keying with preserving
  *"the 'must sit under output_dir' check"*. There is no such check: the relative branch joins
  `output_dir / locator` and then verifies the record's `run_id`, which a symlink under `output_dir`
  satisfies. Not a hole (the `run_id` comparison and now the containment check both still run), but
  the sentence names a guard that does not exist as one.
- Also noted, not a finding: `lineage.py:228` and `:351` cite `task-b2-review.md` /
  `task-b3-review.md`. They are the only citations of a review file anywhere in `src/` (74 `task N`
  references pre-exist, so the *task* convention is established; the *review-file* one is new). The
  files are tracked, so the citations resolve.

---

## What I verified by running

### 1. `io.reuse_from` end to end, on my own two-run project

Not the suite's helper: `publishable new`, two `generate experiment` calls sharing one `output_dir`,
hand-written steps, `git commit`, then `uv run publishable run` through the real console script. The
downstream step reads its locator/step/name from `input_dir/spec.json`, so every arm below is a real
`run` on a committed, clean tree with unchanged hashes.

The upstream run published `shared/step01_publish/cohort.json` (run scope) and
`summary/step03_republish/programs/a.json` + `programs/gpt-4.1__seed29.json` (summary scope); its
repeat-scoped step landed at `<run_dir>/step02_measure/`, **not** under `conditions/` — confirming
§ Corrections correction 9's measurement independently.

**All three locator forms read:**

| Arm | Result |
|---|---|
| relative `run_id` + `summary` step + `programs/a.json` | exit 0, `used: ["step03_republish/programs/a.json"]` |
| absolute run-directory path + `programs/gpt-4.1__seed29.json` (interior dot) | exit 0, dispatched as `.json` |
| absolute path to a **symlink** (`results/moved_link` → the run dir) | exit 0, records the **record's** `run_id`; `grep -c moved_link run.yaml` → **0** |

The entries carry exactly four keys — `run_id`, `code_hash`, `parameters_hash`, `used` — and the two
hashes are byte-identical to the upstream's own `run.yaml` values. No fifth key, no new hash
(`grep hash src/publishable/lineage.py` finds only copies).

**Every one of the eleven `E-UPSTREAM-*` codes reached through the real CLI**, each with the class
plan correction 5 ruled (`ArtifactError` for `-NAME`/`-ARTIFACT-MISSING`, `ContractError` for the
other nine), read out of `executions.jsonl`:

`-LOCATOR` (`a/b`) · `-RUNID-MISMATCH` (relative `latest`) · `-REPO-CONTAINED` (both forms) ·
`-RECORD-MISSING` (unknown id) · `-RECORD-UNREADABLE` (unparseable `run.yaml`) · `-RECORD-VERSION`
(`schema_version: "9.9"`) · `-STEP-SCOPED` (a repeat-scoped upstream step) · `-STEP-UNKNOWN` ·
`-STEP-INCOMPLETE` (arrived for free: `latest` pointing at a run whose step had failed) · `-NAME`
(`../../secret.json`) · `-ARTIFACT-MISSING`.

**What survives a refusal — Decision 10, and `every execution paid for, the record lost` did not
happen.** On all thirteen refusing runs: `run.yaml` **exists**, `status: partial`, exit **3**, the
plan **continued** to the next execution (`step02_measure completed` on every one), `latest` was
repointed at the new run, `executions.jsonl` carried one line per step-execution against
`sweep.yaml`'s `execution_order`, and `provenance.upstream == []`.

**Decision 6's two halves, on real runs:** a step that reads and **then** raises → execution
`failed`, `status: partial`, `run.yaml` present, and the entry **kept** with its `used` name; a step
whose `reuse_from` **raises** → `upstream: []` with the execution still recorded `failed` and the
plan still continuing.

**Fixture E independently:** the upstream run itself — no `reuse_from` anywhere — wrote
`upstream: []`, present and empty, in a real `run.yaml`.

### 2. The `latest` asymmetry, all four arms plus the converse

Relative `latest` → `E-UPSTREAM-RUNID-MISMATCH`, message naming *"`latest` is a path, not a run_id"*.
Absolute symlink → **accepted**, resolved id recorded. So the converse holds: a rule refusing both
forms would not pass. Symlink-into-repo → refused in **both** forms (see Major 1). The comparison in
`resolve_run` is `record.get("run_id") != locator` — the locator **as given**, which is what keeps the
asymmetry alive after batch 3 started resolving the relative form's path.

### 3. Containment does not overshoot, on all three readers

Full clause-by-arm matrix, computed by running the three candidate predicates over one real tree:

| arm | shipped | drop `is_absolute` | drop `startswith` | widened (refuse any `/`) |
|---|---|---|---|---|
| `../secret.json` | REFUSE | REFUSE | **read** | REFUSE |
| absolute, outside base | REFUSE | REFUSE | REFUSE | REFUSE |
| absolute, **inside** the step dir | REFUSE | **read** | REFUSE | REFUSE |
| symlink escaping the base | REFUSE | REFUSE | **read** | REFUSE |
| `programs/a.json` | read | read | read | **REFUSE** |
| `programs/gpt-4.1__seed29.json` | read | read | read | **REFUSE** |

Then against the suite: dropping `Path(name).is_absolute()` fails **all three** readers' refusal tests
(`test_read_upstream_…`, `test_read_condition_…`, `test_reuse_from_name_containment_…`) — so batch 3's
"absolute-inside-the-step-dir" repair really did reach all three; widening to refuse any separator
fails **all three positive controls plus Fixture R**. `..` and the escaping symlink each discriminate
the `startswith` clause; absolute-outside carries no weight, exactly as batch 3 found.

### 4. Decision 2 — `output_dir` never reaches `io`, one method and zero fields

By introspection at HEAD against `main` (AST for `main`, live `dir()`/`signature` for HEAD):

- public methods: **+1, `reuse_from`**, nothing else added or removed
- `__init__` keywords: **+1, `upstream`**, stored as `self._upstream` (private, unread by any step)
- no `output_dir` anywhere on `StepIO`; the resolver is built in `command_run` from
  `doc["data"]["output_dir"]` with `repo_root = find_repo_root(config_path)` — the walk-up from the
  path the command was given, per § Invariants, not re-derived from the upstream path
- `src/publishable/__init__.py` and `validate.py` **unchanged** (Decision 11: `validate` gains
  nothing), and the `TYPE_CHECKING` guards in `runner.py`/`artifacts.py` keep the import graph acyclic

### 5. The cache and the ledger key differently — and the docstrings are true of the final state

Probe: one upstream, addressed by its `run_id` and then by an absolute path, with the upstream's
`run.yaml` **edited between the two calls**, then the first locator repeated.

- `read_run_record` calls: **2** (one per distinct locator; the repeat was a cache hit)
- `code_hash` returned per `resolve()`: `AAAA`, `BBBB`, `AAAA`
- ledger entries: **1**, carrying `AAAA` and both `used` names

So the brief's clause *"two locators addressing one run give one ledger entry **and one record
read**"* is stale — the batch-3 fix round re-keyed the cache **by locator** (`292c236`), which makes
it two reads, and `UpstreamLedger.record`'s docstring says so explicitly (*"two distinct locators
naming the same run still reach `resolve()` twice, once each"*). Reporting as a note, not a defect:
the code is primary and the ledger's `setdefault` is what still delivers Decision 6's record-level
*one answer per run*. Every docstring I checked against the final state is true: `UpstreamLedger`'s
"keyed by the RESOLVED `run_id`", `record`'s "copied the first time this `run_id` is seen and never
re-read", `resolve`'s "at most once per distinct LOCATOR", and `_contained`'s "the same symlink-aware
technique `_resolve` already uses" (verified: the two predicates are identical — which is Minor 2).

### 6. The guard pin's whole life

All four arms green (`arm_a`, `arm_b`, `arm_c` in `test_cli.py`; `arm_d` in `test_artifacts.py`).

**The deletion sweep is exhaustive, not sampled** — this is the check the named-editor mechanism
exists to make possible, so it was run over the whole of `tests/` rather than over the arm:

- `git diff main..HEAD -- tests/ | grep -c '^-[^-]'` → **0**. Across all twelve tasks, **not one
  line was removed from `tests/`** — which also independently reproduces batch 4's
  "+4-with-zero-deletions" result for the two shipped readers, from the other end and over the
  whole branch rather than one commit.
- `git diff 1f55711..HEAD -- tests/ | grep '^-'` (since the pin) prints **fourteen lines and no
  others**: arm A's docstring reword, arm B's rename and docstring, and the single authorized
  assertion swap `assert "upstream" not in provenance` → `assert provenance["upstream"] == []`.
  Nothing reordered, no other assertion moved, in either file.

The one-key append lands in **both** places the twelve-key list is pinned — the task-11 arm B *and*
the shipped H7d `test_a_run_with_no_declared_probe_records_a_null_apparatus_block_and_no_ledger`.
Adding one spurious key to `command_run`'s provenance dict **fails both pins**.
Arm C — Decision 4's foundation — is genuinely breakable: routing `summary` into `shared` inside
`run_record._execution_block` fails it and nothing else in the selection.

Also caught, each by mutation: deleting `sorted()` on `used` (Fixture O), deleting `sorted()` on the
entries (Fixture O's second arm), and writing `upstream` only when non-empty (fails Fixture E **and**
both key-list pins).

### 7. § Invariants

- **`input_dir`/`output_dir` never inside the repo**: enforced on **both** locator forms, verified end
  to end (Major 1 is that the documents say otherwise, not that the code does)
- **Three hashes**: nothing hashed here; `provenance.upstream` carries copies of the upstream's own
  two figures plus `run_id` and `used`. No fourth hash, no manifest over the artifacts read
- **One import root**: `publishable/__init__.py` untouched; `UpstreamResolver` is not exported
- **Core never inspects user Python / greenfield**: the locator is a parameter value read by the
  step; nothing parses a step body; no `adopt`-shaped surface

### 8. The figures

Re-measured **independently of the entry**, by reading the analysis's own YAML blocks: eight
`statistics` blocks are shown (E3 has none), and seven of them declare a non-null
`statistics.resample` **and** a non-empty `statistics.report_by` — E1, E2, E4, E6, C1, C2, C3.
**E5 is the can-fail control and it does differ**: `resample: null`, `report_by: []`. The **7** is
right, and it is still H4's, live, and unmoved by this slice.

The new § Executability entry quotes the 2026-08-20 correction-to-the-correction's four-row table with
**exactly one row moved** (`io.reuse_from` 6 → 0); rows 1, 3 and 4 are repeated verbatim. **No fifth
number is minted**, nothing says "N configs now execute", and the entry states in its own text that it
may not claim E3/E4/E6 executes and that every claim it makes about a config is invisible to
`validate`. The design's own third payoff row ("8 of 8 transplantable, projected") was refused by the
plan (correction 1) and **does not appear** in the shipped entry — confirmed by grep. The entry's
`254aabe` citation is honest: `git diff 254aabe..HEAD -- src/ tests/` is **empty**, so the code state
measured is HEAD's.

### 9. The documents

- **The eleven `E-UPSTREAM-*` codes enumerated from the code first** (`grep 'code="E-UPSTREAM'` over
  `src/`), then confirmed in `reference.md`: all eleven present, each twice (the § Lineage prose and
  the § Errors table), and the reverse direction is exact — no code named in the document that the
  code does not raise. Control: a bogus code returns 0.
- `E-ARTIFACT-NAME`'s widened row claims **three emit sites**; the code has exactly three
  (`artifacts.py:699` write-side `_resolve`, `:803` `read_condition`, `:868` `read_upstream`).
- § Package layout no longer marks `lineage.py` unbuilt; `artifacts.py`'s gloss gains `reuse_from`;
  no stale `not yet built` marker anywhere near lineage in the four documents.
- `ArtifactError`'s gloss fixed in **both** places (`errors.py:16` and the § Errors exception tree).
- **The worked example is untouched** — no `cohort-pilot` number, hash prefix or interval moved; the
  `run.yaml` example's `upstream` block pre-exists on `main` and shows the same four keys the code
  writes.
- **Mechanical pass over README, `design-principles.md`, `experimental-designs.md`, `reference.md`,
  the feasibility analysis and `CLAUDE.md`** (links, cross-file `#anchor`s, duplicate anchors, table
  column counts, empty rows, trailing whitespace, tabs, invisible unicode; fenced blocks skipped;
  escaped `\|` handled): **0 problems**. **Proved able to fail**: injecting one 3-cell row under a
  2-cell header and one dangling `#anchor` into `reference.md` produced exactly those two reports, and
  the file was restored and re-diffed to empty.
- Cross-document classes: no config field added, so § The one config file is unaffected; no enum
  comment, version, or *prevented mistake* touched; the `provenance` key-order divergence between
  `cli.py` and § The two files is the pre-existing one the `spec-defects.md` note already covers, and
  the amendment says so accurately.

### 10. The filings

- `io.reuse_from is unbuilt and unowned` — **struck**, and its own citation corrected: *"reference.md
  § Steps that consume an earlier run's artifacts"* names no heading anywhere. Verified: that phrase
  occurs once in the repo, as a **table cell** in `experimental-designs.md:378`.
- `provenance.upstream` census row — struck, with an explicit pointer past the dated 2026-08-13
  paragraph whose own last sentence still calls `upstream` unwritten. Correct disposition (dated,
  superseded in the same file, not retro-edited).
- `report_by` under `resample` — **re-scoped to seven configs**, owner unchanged (H4). I re-measured
  the seven independently (§ 8).
- `resolve_run`'s relative-form containment gap — **closed**, with the second half (returning a
  resolved path) separately pinned after batch 3's review found the first pin did not cover it.
- Two new filings both state **the check their owner must make**: `UpstreamLedger.record`'s
  `.get`-copied `None` hash (owner **H9**, secondarily **H8b**, with the two competing readings
  spelled out) and `resolves_inside_repo`'s fail-open on an unresolved `repo_root` (owner
  **unassigned**, with the reason attached — no shipped caller can reach it, and it is the function's
  own gap rather than any slice's). Neither is "whoever does X".

---

## The one question batch 6 left open, ruled here

Batch 6 is the only batch with **no review** (`task-b6-review.md` does not exist), and it owns tasks
8, 9 and 10 — which is why items 8, 9 and 10 above were re-measured from scratch rather than read.
Its § Concerns asks for a controller decision on `spec-defects.md`'s census table (§ *"23 entries"*),
whose H6 row still says *"the six unwritten `run.yaml` keys (its allocation half is H3, its **upstream
half H8**)"* while two of those six are now closed.

**Ruled: no edit, and batch 6's disposition stands.** The table says of itself *"which is a census and
not a work plan"* and *"A slice picking up an entry should read the whole entry rather than this
table"* — so it is an index, dated by construction, and the entry it indexes carries the closure as a
struck row plus a dated amendment. Re-tallying it would rewrite a historical count to keep a
self-disclaimed index current, and the cheaper direction here is the one this repo prefers: leave the
label, since the reader it routes lands on the amended entry. Recorded as decided rather than left
open, which is the point of ruling it.

---

## What I could not check

- **Whether an `E-APPARATUS-FACT-*`/`-RETURN` contract refusal raised mid-plan loses the accumulated
  ledger with `run.yaml`.** That path (`cli.py:2528-2546`) returns before phase 9, so it would — but
  it is H7d's pre-existing behaviour for the whole `provenance` mapping, not something H8a introduced,
  and reaching it needs a probe plugin. The two stop paths I could reason about are safe: a mid-plan
  stop with ≥1 result falls through to phase 9 and writes `upstream` with its entries; a zero-result
  stop returns early, and with zero results no execution ran, so no read can have been lost.
- **The `latest.txt` fallback branch** — this machine writes a real symlink (confirmed: my
  `results/latest` is one), so the no-symlink path is unexercised here, as the plan already records.
- **Whether any real user step reads an artifact through a `..` segment.** Measured only over what
  this repo can see. Task 12's +4-tests-with-zero-deletions result is the strongest available
  evidence that nothing in-tree did.
- **Whether E3/E4/E6 have dependencies inside a step *body***. No `growth_screen` plugin exists; this
  is the standing limit every § Executability entry names, and the entry names it again.

---

## Tree state

Clean. Every mutation above was applied from a byte-compared backup and reverted by copying the
backup back, then confirmed by `md5` **and** by `git status --porcelain` being empty of tracked
changes — never with `git checkout --`. The full suite was re-run green after the last revert.

`task-b5-review.md` was untracked at the start of this review (the `sdd-workspace` gitignore clobber
`CLAUDE.md` warns about; `.superpowers/sdd/.gitignore` itself is intact). It and this file are
committed with `git add -f`.
