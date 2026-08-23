# H9b — `resume`: what a run must make durable so a second entry can continue it — design

**Written 2026-08-23 against `main` at `1daf3b4`** (the H9a merge), clean tree. Every measurement
below was made by reading or running at that commit and says which. Nothing is carried from
[`H9-SCOPING.md`](../H9-SCOPING.md) without re-checking; where this design disagrees with it the
disagreement is named in § Where this design disagrees with the scoping rather than silently
corrected. **A scoping expires and a spec does not**, so the figures here replace its figures where
they differ — and one of its central claims is falsified below, which is why that section is the
first thing to read after the rulings.

H9b is the second of H9's four parts. Unlike H9a it builds **a new record**: `resume` cannot exist
unless `run` makes durable, before it executes, things that today live only in memory. That makes
this slice **not additive**, and § Is this additive? — the disclosure enumerates the six things that
move.

Every project, roster, crashed run directory and race probe built for this design lives under the
session scratchpad, **outside this repository** — H6a made the dirty gate load-bearing, so a
creation command run inside the tree would dirty what that gate reads.

---

## 0. What was measured, before any decision

| Fact | How |
|---|---|
| A real crashed run directory holds `config.yaml`, `environment/{pyproject.toml,repo_root.txt}`, `executions.jsonl`, `lock`, `manifest/input.json`, `sweep.yaml`, the partial per-repeat trees — and **no `run.yaml`, no `latest` pointer** | Built one: a scaffolded project outside the repo, 2 conditions × 4 seed repeats over 6 units, whose repeat step calls `os._exit(9)` on its third execution. Reproduced from a file counter, so the crash point is deterministic |
| `lock` holds **two** keys, `{"host": "macbookair.lan", "pid": 41271}` | `cat` on that directory. § One execution at a time says it *"records the host, pid, and start time"* — `run_identity.RunLock.__enter__` writes two |
| The run ID's 7-hex suffix **is** a real `code_hash` prefix | Directory `run_2026-08-23T18-35-18Z_ef9073c`; recomputing `code_hash_of(hashed_files(root, unignored_under_hashed_trees))` in the same tree gives `sha256:ef9073c4…`, `short` → `ef9073c`, over 6 files |
| `code_hash` has **one** call site in `src/` and is written only into `run.yaml` | `grep -n` over `src/publishable/cli.py`: `ch = code_hash_of(hashed)` at one line, read at `assemble_run_yaml` |
| All four identity figures exist **before** the run directory is created | `ch`, `ph`, `manifest`, `lock_hash` are `Prepared` fields; `manifest_hash(manifest)` is a pure function of the dict. `Prepared` is built by `_prepare_run`, which returns before `allocate_run_dir` is called |
| `run_status`'s bare `assert len(results) >= planned` fires on a short list | `run_status([], planned=8, stop=None)` → `AssertionError: execute_plan returned 0 results against a plan of 8…`; the same call with `stop="max_failed_fraction"` returns `"failed"` |
| `verify_manifest(input_dir, manifest)` compares the input directory against **the manifest it is handed** | Read, `manifest.py`. Its one call site passes the manifest `_prepare_run` just built, so on a resume it would compare *now against now* and always come back clean |
| The aggregate phase reads `ExecutionResult.rows`, `.recorded`, `.skipped` and `.returned` — **not** any file | Read, `cli.py` phase 8: `recording_steps` is `{… if r.rows}`; `collapse_repeats(results, …)` and `_condition_counts(results, …)` take the results list; `_gather_repeats` walks `r.rows`/`r.recorded`; `attrition` walks `r.recorded`/`r.skipped` |
| `units.parquet` is written **only** when a step recorded at least one row | Read, `artifacts.finalize`: `if self._rows:` |
| `units.parquet`'s columns are `unit`, then every declared attribute, then every recorded key — deduped by name, **recorded value winning a name collision** | Read, `artifacts._finalize_columns` and `finalize`'s merge loop (`merged[name] = row.get(name)` runs after the attribute loop) |
| `ineligible.jsonl` holds one line per skipped unit, written only when there is one | Read, `finalize`'s trailing loop |
| `_execution_block` writes `"attempts": 1` as a **literal** | Read, `run_record.py` |
| `_gather_repeats` already accumulates rather than overwrites, with *"a resumed leaf re-reported, say"* as its stated reason | Read, `stats.py` |
| `attrition`'s docstring already states *"No per-execution `n` is written in this build"* | Read, `runner.py` |
| Today `publishable resume`, `resume new`, `resume a b` and `resume --json` all print the unbuilt diagnostic and exit **2** | Ran all four through the real console script |
| `apparatus.replay_ledger` reconstructs a baseline `Observations` from `apparatus/probes.jsonl`, filtered to `run_start`/`pre_execution`, and raises `E-FREEZE-LEDGER-UNREADABLE` | Read, `apparatus.py`; its sole caller is `freeze` |
| `identity.json` is a free name | `grep -rn 'identity.json' src/ docs/ tests/` → zero hits |

**Three race probes, because one of this slice's rulings rests on a concurrency claim.** All three
are in the scratchpad, five concurrent OS processes per trial against one run directory holding a
dead holder's lock:

| Protocol | Result |
|---|---|
| Liveness-test, then `os.rename(lock, lock.stale)`, then exclusive create — *"exactly one rename wins"* | **FALSIFIED on trial 0**: four of four processes won. The rename's source is re-created by an earlier winner, so a later rename finds the *new* lock |
| Scan for live lock files, then exclusive create at the next generation index | **FALSIFIED on trial 0**: two winners. The flaw is the scan — a decision made from a directory listing is stale by the time the claim is made |
| **Exclusive create of one takeover token (`lock.takeover`), *then* liveness-test, then replace, token released in `finally`** | **60 trials × 5 processes, zero violations**, exactly one winner every trial, with both refusal shapes observed (`REFUSE-live` 4×/trial and `REFUSE-takeover-held` in 34 of 60 trials) |
| The same with the token's exclusive create **deleted** — the positive control | **Violation at trial 22**: two winners. So the token is load-bearing and the probe can fail |

The third is Decision 2's mechanism, and the fourth is why it is not merely asserted.

---

## 1. The three controller rulings

### Decision 1 (Ruling V) — a run makes its identity claims durable before it executes, in `identity.json`, and `resume` refuses `E-RESUME-NO-IDENTITY` when the file is absent

**Question.** § Resuming says `resume` *"refuses if `parameters_hash`, `code_hash`, or `uv.lock` don't
match current state."* A crashed run directory holds no `run.yaml`, so what are the operands?

**Answer.** `run`, `draft` and `resume` write `<run_dir>/identity.json` at run start, inside the
lock, beside `config.yaml` — one JSON object, five keys, never rewritten:

```json
{
  "code_hash": "sha256:ef9073c4…",
  "parameters_hash": "sha256:72634707…",
  "uv_lock_hash": null,
  "config_path": "configs/cohort/config.yaml",
  "draft": false
}
```

A run directory without it cannot be resumed: `resume` prints `E-RESUME-NO-IDENTITY` and exits `1`,
naming the reason (a build that predates the artifact, or a directory edited by hand) and the remedy
(run again into a fresh `run_<id>/`). **It does not fall back to the run ID's hash prefix**, and it
does not guess.

**Grounds, measured.** Three of the four figures § Resuming's sentence needs are recoverable from a
crashed directory and one is not — `code_hash` has exactly one call site in `src/` and is written
only into `run.yaml`. The only surviving trace is the directory name's 7 hex characters, and
recomputing the hash in the crashed project reproduced them exactly (`ef9073c`), so a prefix
comparison is a *real* comparison. It is nevertheless rejected below. And § `config.yaml` and
`environment/repo_root.txt` already states the underlying fact for `freeze` — *"`code_hash` at run
start is not recoverable from a tree that has since moved"* — so § Resuming and that sentence cannot
both hold as written; this decision is what makes them both true.

**This extends H8b's pattern rather than inventing a second one.** H8b Decision 7 added `config.yaml`
and `environment/repo_root.txt` at run start for exactly this reason, and § The other files a run
writes already carries the category: *"settled before the first execution and never touched again."*
The new file joins that sentence's list. **Copied where they sit, not only what they call**: the two
H8b artifacts are written inside `with RunLock(run_dir)`, before `sweep.yaml`, and `identity.json` is
written in the same block in the same order — not later, and not outside the lock.

**Why five keys, and why not more.** The rule is: **exactly what a second entry cannot compute and
cannot wait for `run.yaml` to hold, and nothing it will not read.**

- `code_hash` — not recoverable at all. The reason the file exists.
- `parameters_hash` — recomputable from a config file, and that is the point: the recorded figure is
  what makes an *edit* detectable. This is also the operand the standing filing about `freeze` asks
  for by name (Decision 15).
- `uv_lock_hash` — `environment/uv.lock` is a byte copy and therefore editable; the recorded digest
  is what a comparison rests on. `null` when the project resolved no lockfile, which a scaffolded
  project does not (`W-ENV-UNLOCKED`, measured on the crash fixture — no `environment/uv.lock`
  exists there at all).
- `config_path` — the config's path **relative to the repo root**. Without it a resume cannot find
  the file the run was started from, and the run-directory byte copy is not a substitute: phases 1–5
  key off the config *path* in four places (`find_repo_root(config_path)`,
  `git_provenance(config_path, config_path)`, `E-NAME-DIR`, and the
  `input_dir`/`output_dir`-not-in-the-repo checks), and the copy sits under `output_dir`, which may
  never be inside the repo. Re-entering `_prepare_run` on the project's own file is what makes
  `resume` run *the identical phases 1–5* rather than a variant of them.
- `draft` — because **a resumed draft that recorded `draft: false` would be citable.** `draft: true`
  is the flag all three readers key on (`report.py` twice, `diff.py` once), it exists nowhere at run
  start today, and a `resume` that could not read it would either have to refuse every draft or
  publish a laundered record.

**`input_manifest_hash` is deliberately absent.** `manifest/input.json` is itself the durable
operand, so recording its digest would add a figure with no reader — *an unbuilt reader of a shipped
surface*, in the mint-it-yourself direction. Decision 8 says what `resume` does with the manifest
instead, and the § Errors row for `E-RESUME-INPUT-MOVED` names the comparison so the absence is not
read as an oversight.

**Alternatives rejected.**
*Compare the run ID's 7-hex prefix.* It is 28 bits, it is not injective across runs (a same-second
collision takes a `_b` suffix and keeps the same prefix), and — decisively — it says **nothing** about
`parameters` or the lockfile, so two of § Resuming's three comparisons would remain unanswerable. A
comparison that covers one of three figures is worse than a refusal, because it reads as three.
*Narrow § Resuming to the two figures a directory can already answer.* This was seriously weighed and
is the cheapest answer. It loses the comparison that matters most: the one § Resuming's own draft
paragraph rests on, and the one that catches *"I edited the code and then resumed."*
*Write a partial `run.yaml` at run start.* § What status means makes a `run.yaml`'s presence mean *the
run ended* — that is what `resume` distinguishes itself against, and `report`, `diff`, `study` and
`freeze` all key on it. Writing one early would break four shipped readers to save one file.
*Put the figures in `sweep.yaml`.* § `sweep.yaml` — the resolved plan is *"the answer to what this run
was going to do"* — a plan, not an identity claim; and `design_digest` is already documented there as
*"a derivation input, not an identity claim"*, which is the distinction this would blur.

**Cost if wrong.** A run directory that cannot be resumed and cannot say why — which is worse than a
`resume` that refuses loudly. That is why the absence is a **named code with a remedy** rather than a
silent fallback, and why the file is written **before the first execution** rather than at the first
checkpoint: a run that dies in its first execution is exactly the run `resume` exists for.

### Decision 2 (Ruling W) — `resume` takes over a lock whose holder is not alive, behind one exclusive takeover token, and refuses `E-RUN-LOCKED` whenever it cannot tell

**Question.** The commonest crash leaves `lock` behind — measured. `E-RUN-LOCKED` therefore fires
before any hash comparison, and `--force` is forbidden by *"operation commands take paths and nothing
else."* What is the route out?

**Answer.** `resume` — and only `resume` — may reclaim a run directory whose lock holder is provably
dead. The protocol is, in order, and the order is the whole of its correctness:

1. **Claim the takeover, atomically, before deciding anything.**
   `os.open(run_dir / "lock.takeover", O_CREAT | O_EXCL | O_WRONLY)`. `FileExistsError` →
   `E-RUN-LOCKED`, naming the concurrent takeover. Released in a `finally` that runs on every path,
   `BaseException` included.
2. **Inside the token, read `lock` and test liveness.** Absent → nothing to reclaim, go to step 4.
3. **Refuse unless the holder is provably dead.** Dead → `unlink(lock)`.
4. **Take the lock the ordinary way** — `RunLock(run_dir)`, byte-unchanged, whose `O_CREAT|O_EXCL` is
   still the only claim in the system. `FileExistsError` → `E-RUN-LOCKED`.

**The liveness test, and it refuses in every case it cannot answer:**

| State of `lock` | Verdict |
|---|---|
| Not valid JSON, not an object, or missing/mistyped `host` or `pid` | **held** — cannot tell |
| `host` is not this machine's `socket.gethostname()` | **held** — core cannot see another node's process table |
| `os.kill(pid, 0)` succeeds | **held** |
| `os.kill(pid, 0)` raises `PermissionError` | **held** — the pid exists and belongs to another user |
| `os.kill(pid, 0)` raises any other `OSError` | **held** |
| `os.kill(pid, 0)` raises `ProcessLookupError` | **dead** — the only verdict that permits a takeover |

**Grounds, measured rather than argued.** Two plausible protocols were probed first and **both were
falsified on trial 0** — rename-as-mutex (four winners of four) and scan-then-claim (two winners).
Both fail for one reason: a decision taken from the directory's state is stale by the time the claim
is made. The token inverts that order — **contend first, decide second** — and it held for 60 trials
× 5 processes with zero violations, while deleting the token produced two winners by trial 22. *A
safety argument in a comment is a claim*: this one was made to fail before it was believed.

**`lock` gains its third key**, `started_at`, which § One execution at a time already documents and
`RunLock.__enter__` does not write (measured: two keys). It exists for the **diagnostic** — a refusal
that says *held since 2026-08-23T18:35:18Z by pid 41271 on macbookair.lan* is the difference between
a legible refusal and a puzzle. **The liveness test deliberately does not consult it**, and that is
stated in the code and in the document rather than left as a silence: PID reuse therefore reads as
*alive* and refuses, which is the conservative direction. A field recorded and not read would
otherwise be this repo's own named defect class, so the non-use is documented as a decision.

**The residual, stated rather than hidden.** A takeover killed inside its own window — between the
token's creation and the lock's — leaves `lock.takeover` behind, and every later `resume` then
refuses `E-RUN-LOCKED` until it is removed. That window contains **two syscalls and no user code**,
which is the reason the protocol puts nothing else inside it; the `E-RUN-LOCKED` row names the file
and the remedy. This is a stated non-promise, not an unstated one.

**No flags, and no second command name.** `--force` is forbidden by the invariant, a `--force`-shaped
environment variable is forbidden by the same sentence (*"no behavior-changing env vars"*), and a
second positional would make `resume` take an argument that is not a path. **The route is the command
name itself**: `resume` is by definition a re-entry after the first attempt stopped, so *may reclaim a
dead holder's directory* is a property of the command rather than a mode of it — the same argument
§ Draft runs makes for `draft` over `--allow-dirty`.

**Cost if wrong.** Two concurrent resumes into one run directory: two writers on one append-only
tree, which is precisely the failure the lock exists to prevent. That is why the liveness test refuses
in six of its seven states, why the mutual exclusion was probed against a positive control rather
than reasoned about, and why the pin for it (§ The guard pin, arm G) is deterministic rather than
probabilistic.

### Decision 3 (Ruling X) — `E-RUN-LOCKED` and `E-RUN-ID-EXHAUSTED` get § Errors core raises rows, each covering every site that raises **or** reports it

**Question.** Both codes are raised in `run_identity.py` and appear in none of the four documents
(measured: `grep -c` returns `0` in each of `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, with `E-PARAM-MISSING` returning `1` in the same
four-file list as a can-fail control). `E-RUN-LOCKED` is `resume`'s documented refusal. Which table,
and what must the rows say?

**Answer.** **§ Errors core raises**, and the table's own scope sentence is what decides it rather
than this design's convenience. That section's lead says *"Each carries `.code`"* and its `Raised by`
column names raise sites; its own qualifying paragraph already admits two non-raise rows *"and the
`Type` cell says so"*. Both codes are genuine `ContractError` raises, so they need no such
qualification and they belong there. § Errors `validate` reports is the wrong table by its own lead —
*"these are the codes a **command** reports"* as a collected diagnostic — and `validate` neither
locks a directory nor allocates one.

**The rows enumerate every site, because § Errors carries one row per code and not one per emit
site** — the `E-TEMPLATE-UNKNOWN` precedent, where a task scoped by one helper's call site missed the
second:

| Code | Sites, enumerated by reading |
|---|---|
| `E-RUN-LOCKED` | **raised** at `run_identity.RunLock.__enter__` on `FileExistsError`, after reading the holder line; **raised** at the takeover's token claim and at its final `RunLock` acquisition (Decision 2, both in `run_identity`); **reported** at `cli.main`'s `except PublishableError` handler, and — per Decision 13 — **reported** through `resume`'s own credential-bearing `Collector` for every refusal `resume` itself decides |
| `E-RUN-ID-EXHAUSTED` | **raised** at `run_identity.allocate_run_dir` when 26 suffixes are taken; **reported** at `cli.main`. `resume` never reaches it — it allocates no directory — so the row names `run` and `draft` |

**And the row must say where `E-RUN-LOCKED` is reachable, because from `run` and `draft` it is
not** — structurally, not merely unlikely: `allocate_run_dir`'s `mkdir` **is** the claim, so a
directory that already exists sends it to the next suffix and a lock file can never pre-exist a
directory those two just created. `dry-run` takes no lock at all (H9a Decision 12). So `resume` is
the only command from which the code is reachable, and the row says so in those terms.

**Checked against each table's own scope sentence, not against this design's instruction.** H6a's
batch 4 put a row in a table whose scope did not admit it and the review settled the question by
citing the design; H9a then found **thirteen rows narrower than their code and one wider**. So every
row this slice writes — the two above and the fourteen new `E-RESUME-*`/`E-FREEZE-CONFIG-EDITED` rows
of Decision 17 — is placed by re-reading the destination table's lead paragraph first, and the task
that writes them must quote that lead in its report.

**The five-codes filing is amended to three.** `spec-defects.md`'s standing entry says H9 *"touches
neither the run lock's own refusals"*; that clause is falsified by § Resuming's own text and is
corrected in place with the reason, leaving `E-INPUT-CHANGED`, `E-PROJECT-EXISTS` and
`E-EXPERIMENT-EXISTS` unassigned — the manifest path and `generators/`/`scaffold.py` are not H9b's
surface, and taking them because they sit near a file H9b touches is the charter growing rather than
the surface.

**Cost if wrong.** A row narrower than its code, which is this family's single most frequent
documentation defect, and a reader who greps `E-RUN-LOCKED` after a `resume` refuses finds nothing.

---

## 2. What a run must make durable, beyond the hashes

### Decision 4 — the aggregate phase reads `ExecutionResult`, not the disk, so `resume` must reconstitute a **full** result for every triple it skips

**Question.** H9-SCOPING § 4.5 says the durability hole is `per_repeat` alone, and that *"`aggregated`
survives (it is recomputed from `units.parquet`, which is on disk)."* Is that true?

**Answer. No, and this reshapes the whole slice.** Phase 8 reads four fields off the in-memory
results list and no file at all:

- `recording_steps` is `{r.execution.step_name for r in results if … and r.rows}` — a step with no
  reconstituted rows is not even considered;
- `collapse_repeats(results, …)` and `repeats_disagreeing(results, …)` walk `r.rows` and `r.recorded`
  through `_gather_repeats`;
- `_condition_counts(results, …)` → `attrition(results, …)` walks `r.recorded` and `r.skipped`;
- `run_record` builds `per_repeat` from `r.returned` and the `execution` block from `r.status`,
  `r.started_at`, `r.wall_seconds`, `r.error`.

So a `resume` that simply skipped completed triples would publish every interval, every `n`, every
delta and every hypothesis verdict **over the re-executed triples only** — plausible numbers, no
diagnostic, and a `completed` status. That is the worst failure shape in this repository's
vocabulary, and it is not what the scoping predicted.

**What is durable, and what H9b must make durable.** Per skipped (step, condition, repeat):

| `ExecutionResult` field | Source |
|---|---|
| `execution` | the plan `_prepare_run` rebuilt, ordered by `sweep.yaml` (Decision 9) |
| `status`, `started_at`, `wall_seconds`, `error` | `executions.jsonl` — already written |
| `rows` | `<step_dir>/units.parquet`, read back through the shipped `_decode_parquet` reader, **minus** the declared-attribute columns |
| `recorded` | the `unit` column of those rows |
| `skipped` | `<step_dir>/ineligible.jsonl`'s `unit` values |
| `returned` | **not durable today.** Decision 5 |

**The attribute subtraction is a real derivation with a real failure mode**, and naming it is the
point. `finalize` writes `unit`, then every declared attribute, then every recorded key, deduped by
name — and when a recorded key collides with an attribute name the **recorded value** is what lands
in the file. So subtracting attributes *by name* would drop a genuine recorded column, which is
exactly the *reserved name standing in for a structural fact* proxy this repo has already paid for
once. Decision 5's `recorded_columns` is what makes the subtraction structural instead.

**Cost if wrong.** Published intervals computed over a fraction of the units, at exit `0`, with
nothing in the record marking them. The fixture that guards it is a whole-record equality rather than
a set of per-key assertions (§ Fixtures as claims, Fixture A).

### Decision 5 — `executions.jsonl` gains `returned` and `recorded_columns`; `attempt` and `n` are deleted from its documented example

**Question.** § `executions.jsonl` documents eight keys including `attempt` and `n`, neither of which
is written; the code writes `scope` and `error`, neither of which is documented (measured, both
directions). Which side moves?

**Answer.** Both, in different places. The line the code writes gains **two** keys and the document's
example is rewritten to the ten the code will write:

```json
{"step": "step03_analyze", "scope": "repeat", "condition": 1, "repeat": "seed17",
 "status": "completed", "started_at": "2026-08-06T14:03:27Z", "wall_seconds": 903.1,
 "error": null, "recorded_columns": ["pred", "status"],
 "returned": {"r": 0.607, "n_pairs": 228}}
```

- **`returned`** — *"exactly what the step returned"*, which is the one thing `per_repeat` is built
  from and the one thing no file holds. It is serializable **by invariant**, not by luck: a step's
  `run` returns a flat mapping of scalars, and `coerce_scalars` has already run by the time the line
  is written. The one exception is a `summary`-scope `Estimate`, so the value is written through
  `run_record.summary_values` — **the sibling that already got it right**, and the same expansion
  `run.yaml`'s summary block uses, so the two cannot disagree. It is idempotent on an
  already-expanded mapping, which is what makes reading it back safe.
- **`recorded_columns`** — the union of recorded column names for that execution, which is what makes
  Decision 4's attribute subtraction structural: the recorded columns are *named*, so everything else
  in `units.parquet` is `unit` or an attribute, whatever it is called. It also carries the one
  distinction no other artifact can: **an empty list means the step recorded nothing** (a scalar-only
  repeat step, for which `finalize` writes no `units.parquet` at all), which is a different state from
  a missing file, and reconstitution must not conflate corruption with a legitimately empty table.
- **`attempt` is deleted from the document, not built.** § Resuming already defines `attempts` as *the
  number of records the triple has in `executions.jsonl`* — so writing it into each line would be a
  derived figure stored in an append-only log, i.e. a second source of truth for a count the log
  already answers. Decision 6 computes it from the log instead.
- **`n` is deleted from the document, not built.** `runner.attrition`'s own docstring already states
  *"No per-execution `n` is written in this build"*, and § Repeat kinds is where the per-execution
  triple is described. Writing it would mint a per-execution figure no reader asks for, in the slice
  that is trying to shrink what is unread.

**And § `executions.jsonl`'s load-bearing claim becomes true.** It says `run.yaml`'s `execution`
block *"is this file folded into the scope nesting, which is why the two never disagree"* — a claim
that **cannot hold for a resumed run** unless the ledger carries what the block is built from. After
this decision it does. That sentence is the reason this decision is here rather than in a document
task.

**Cost if wrong.** `returned` is a step's own return value, so a step returning something huge grows
the ledger. Bounded by the invariant — a flat mapping of scalars — and the alternative is a
`per_repeat` hole exactly where the previous attempt's numbers were.

### Decision 6 — `attempts` becomes a count of ledger records, and `run_status`'s bare assert is **satisfied by construction** rather than changed

**Question.** `_execution_block` writes `"attempts": 1` as a literal, and `run_status` holds
`assert len(results) >= planned` whenever `planned` is given and no stop reason is — measured to fire
on a short list. Both meet `resume` on its first invocation. What moves?

**Answer.** `attempts` is computed from the ledger; the assert is **not touched**.

`assemble_run_yaml` gains one optional argument — a mapping from (step, condition, repeat) to the
number of records that triple holds in `executions.jsonl` — defaulting to `None`, in which case
`_execution_block` writes `1` exactly as today. **For a plain `run` the two are identical, and that is
measured rather than asserted**: every triple has exactly one record, so the count is `1`. This is why
the change is additive for `run` and why the disclosure says so with a measurement behind it.

**The assert stays because `resume` satisfies it.** `resume` passes `planned=len(full_plan)` and a
`results` list holding the reconstituted skipped triples **plus** the re-executed ones — so the list
is as long as the plan whenever the plan ran out, and short only when a stop reason was recorded, which
is the one case the assert already excludes. Its docstring's claim — *"a short list with no recorded
stop reason is a core defect"* — therefore stays **true of `resume` too**, which is the strongest
available evidence that Decision 4's reconstitution is the right architecture: an architecture that
forced this assert to be relaxed would be one that had given up on the previous attempt's results.

**H7d Part B's `max_failed_fraction` pin is left alone**, and this is where it is checked rather than
where it is discovered. That pin holds that a truncated plan reports `completed` at exit `0`, with a
written justification in a shipped test's docstring, and it is filed with its owner told to argue
against that justification. `resume` re-enters the same loop: a resumed run whose own
`max_failed_fraction` stop fires sets `stop.reason`, `run_status` returns `_STOP_REASON_TO_STATUS`'s
answer, and **nothing about the pinned behaviour changes**. Editing that assertion — or its
justification — in a slice about `resume` would be indistinguishable from weakening a pin to make a
resumed truncation tidier, so the task section forbids it by name.

**Cost if wrong.** A resumed run reports `attempts: 1` for a triple that ran three times, which is
§ Resuming's own worked promise; or the assert fires on a legitimate resume and every completed
execution is lost to an `AssertionError`. The second is why arm A of the guard pin is a
resume-to-completion golden and not a unit test of `run_status`.

### Decision 7 — `resume` re-enters `_prepare_run` on the **project's** config, and that is what discharges the `resolve_contrasts` precondition for free

**Question.** `_execute_prepared` needs 36 values. Where do they come from?

**Answer.** From `_prepare_run`, run again — on `repo_root / identity.json["config_path"]`, where
`repo_root` is `environment/repo_root.txt`'s one line. Phases 1–5 are re-run in full: `validate`, the
dirty gate (relaxed exactly when `identity.json["draft"]` is true), the entrypoint import, the
roster, the repeat plan, the hashes, the manifest. The recorded figures are then compared against the
recomputed ones, and a mismatch refuses **before** the lock is taken and before anything executes.

**Grounds.** The alternative — hand `_prepare_run` the run directory's `config.yaml` byte copy plus an
explicit `repo_root` — was weighed and rejected on the invariant: *"which repo is decided by a
walk-up from the path the command was given, not from the working directory"*, and the path `resume`
is given is a run directory that may never be inside the repo. A second entry that supplied its own
repo root would be a second answer to a question the walk-up already owns. Re-entering on the
project's own file means `resume` runs **the identical** phases 1–5, including `E-NAME-DIR` and the
`input_dir`/`output_dir` containment checks, rather than a variant that has to be kept in step.

**A recorded path that escapes the repo root is refused on read.** `config_path` is stored relative,
and containment is checked when it is resolved — H8a's lesson, where a `name` documented as a
relative path would have resolved `../../secret/x.json`. Forward separators stay legal; the rule is
containment only.

**The `resolve_contrasts` precondition is discharged by construction.** `spec-defects.md`'s
S4c-task-9 entry names H9 as the owner of a precondition: a caller reaching
`contrasts.resolve_contrasts` without `validate_config` in front of it would crash on an unhashable
side. `resume`'s phase 1 **is** `validate_config`, through the same `_prepare_run` H9a's `dry-run`
uses, and `resolve_contrasts` is reached only from `_baseline_comparisons`/`_declared_comparisons` in
phase 8 — after it. So the cheaper of the entry's two answers is taken again, `contrasts.py` is
untouched, and the entry is **amended rather than struck**, because H9c's `reproduce` is still bound.

**Cost if wrong.** A resume that validates a different file from the one the run executed, which is
the *"resuming into a different experiment"* failure § Resuming names as the thing it guards against.
Guarded twice: the recorded `parameters_hash` must match, and the plan cross-check of Decision 9 must
agree.

### Decision 8 — the input manifest is compared, not rebuilt, and the **recorded** manifest travels into phases 6–10

**Question.** `verify_manifest` compares the input directory against the manifest it is handed
(measured). On a resume, `_prepare_run` builds a fresh one, so phase 8 would compare now against now
and always come back clean. Do the inputs get checked?

**Answer.** Twice, and neither is `verify_manifest`'s job.

1. **Before the lock:** `manifest_hash(fresh)` against `manifest_hash(recorded)`, read from
   `manifest/input.json`. A mismatch is `E-RESUME-INPUT-MOVED`, exit `1` — the inputs moved between
   the original run start and this resume, so every execution already recorded is over a dataset that
   no longer exists, and § What status means already says there is *"no honest way to report that as
   `partial`."* Refusing before executing is the cheap form of the same judgement.
2. **During the resumed run:** the **recorded** manifest is what travels into phases 6–10, so phase
   8's `verify_manifest` asks the question it was written to ask — did the inputs move while *this*
   attempt executed — and `run.yaml`'s `input_manifest_hash` is the original run's figure rather than
   a second one.

**`E-INPUT-CHANGED` is not reused and its row stays unassigned.** That code is phase 8's
end-of-run re-verification and answers a different question; adding a `resume` emit site to a code
with no § Errors row would be documenting unassigned work in passing.

**Cost if wrong.** A resumed run publishes a record whose `input_manifest_hash` claims a dataset it
did not measure. The pin is an equality on the recorded figure across a crash-and-resume pair.

### Decision 9 — `sweep.yaml` is read rather than re-derived, and the plan is cross-checked before anything runs

**Question.** § Resuming: *"It takes the execution order from `sweep.yaml` rather than re-deriving
it."* What does that mean for a plan `_prepare_run` just rebuilt?

**Answer.** `resume` rebuilds the plan (it must — `Execution` objects are not on disk) and then
**orders it by `sweep.yaml`'s recorded `execution_order`**, never by re-realizing the shuffle. Before
that it cross-checks the recorded `conditions` list against the re-expanded one over the full
four-tuple `index`/`label`/`values`/`is_baseline`, in recorded order — `E-RESUME-PLAN-MISMATCH` on any
disagreement, `E-RESUME-PLAN-MISSING` when the file is absent, unparseable, or holds no `conditions`
list.

**Grounds.** The cross-check is `freeze`'s `E-FREEZE-PLAN-MISMATCH`, and the four-tuple is its
measured shape rather than a choice — `values` is what determines the cfg an execution runs under,
and a two-field check would miss it moving under `ablate` or a declared `baseline`. **The sibling that
already got it right**; `resume`'s stake is higher than `freeze`'s, because `freeze` reports and
`resume` executes. Under a `batch` level the ordering is load-bearing rather than tidy, and § Resuming
says why: batches are positions in time, so a resume free to pick its own order could open batch 4
while batch 3 still had executions outstanding.

**Cost if wrong.** A resumed run executes in an order its own `sweep.yaml` denies, and the record of
the order becomes false — the *"a fact should not be re-computable to a different answer"* failure
§ Resuming names.

### Decision 10 — `allocation.json` is read rather than re-drawn, and the reader the document says does not exist is built here

**Question.** § Resuming states the rule and then states that it *"has no reader in this build"*.
Whose is it, and what does the reader do?

**Answer.** H9b's, uncontested — H3c-3's scoping puts it outside its own slice by name. `resume`
reads `allocation.json` when present and **overrides** the arm memberships and the holdout partition
`_prepare_run` just resolved, through `dataclasses.replace` on the frozen `Prepared`. The fold
partitions come from `sweep.yaml`'s own `partitions` block, which is already written there. A recorded
membership naming a unit the roster no longer holds is `E-RESUME-ALLOCATION-STALE`.

**Grounds.** § Resuming's own escalation: while `by_attribute` was the only executed method, a
re-derivation re-read the same column and cost nothing but tidiness; **a drawn axis leaves no
column**, so a second draw is a second allocation. `assign.<axis>.seed` makes agreement *likely* — and
"likely" is the wrong property for the record of which patient was in which arm. The reader is
therefore tested over a **drawn** axis, where a second draw would differ, and not over
`by_attribute`, where the two readings coincide and the fixture would test one of them twice.

**Cost if wrong.** A resumed run's `allocation_hash` no longer covers the memberships its executions
ran under, and the file that answers *"which patients were in the treatment arm"* becomes false while
its hash still validates.

### Decision 11 — the apparatus baseline is replayed from `apparatus/probes.jsonl`, and `resume` gets its own code rather than printing a `FREEZE` one

**Question.** § The apparatus core can only observe gates every pre-execution probe against the
**first answered** observation, which `run.yaml` carries — and a resumable run has no `run.yaml`. Is
the baseline recoverable?

**Answer. Yes, and no third artifact is needed** — the one durability question in this slice that
answers *yes*. `apparatus.append_observation` writes each line **at the probe call**, so the ledger is
durable across exactly the crash `resume` exists for, and `apparatus.replay_ledger` already
reconstructs the baseline `Observations` from it, filtered to `run_start`/`pre_execution` and replayed
through the shipped `Observations.record`, so the first-answered rule, the per-condition scoping and
the `null` transitions all come along. `resume` threads that replayed `Observations` into the
`Observer` it builds, so a resumed execution is gated against the **original** run's first-answered
facts rather than against its own first probe.

**Two things follow, and both are decisions rather than wiring.**

`replay_ledger`'s refusals are named for `freeze` — its sole caller raises
`E-FREEZE-LEDGER-UNREADABLE`. **`resume` gets its own code, `E-RESUME-PROBES-UNREADABLE`**, and the
shipped code is **not renamed**: a `FREEZE` code printed by a command that is not `freeze` is a lie
about which command found the fault, and renaming a shipped diagnostic breaks a grep a user may
already have — § Exit codes' own rule is that the identifier is the contract. So `replay_ledger` grows
a code parameter defaulting to the shipped value, which keeps `freeze` byte-identical.

**An absent or empty baseline is legitimate for `resume` and a refusal for `freeze`, and the refusal
must not be inherited by copy.** `replay_ledger` returns an empty `Observations` for a missing file
deliberately, because *"there is no baseline"* is `freeze`'s own `E-FREEZE-LEDGER-MISSING` to report —
probing then would pin a fact the run never adopted. For a `resume` that is the ordinary case: a run
that crashed before its first probe has no baseline, and its next execution is entitled to set one
exactly as the original run's first probe would have. So `resume` mints no missing-baseline refusal at
all.

**Cost if wrong.** Either a resumed run's first probe silently becomes the baseline — retiring the
apparatus gate for the whole remainder of the run, which is the one guard that stops a run measured
through two different apparatus states — or a legitimate resume of a run that never probed is refused
for a state that is not a fault.

### Decision 12 — a resumed draft stays a draft, and the dirty gate follows the record rather than the tree

**Question.** `draft: true` exists nowhere at run start today. What does `resume` do with a crashed
draft?

**Answer.** It reads `identity.json["draft"]`, passes it as `allow_dirty` to `_prepare_run` and as
`draft` to `_execute_prepared`, so a resumed draft relaxes the gate exactly as `draft` does and its
`run.yaml` records `draft: true`. A resumed `run` enforces the gate.

**Grounds.** Anything else is a laundering path: a resumed draft that recorded `draft: false` would
be citable, and `report`'s refusal, `study`'s bundle flag and `diff`'s per-side label would all read
it as a final result. And § Resuming's draft paragraph becomes **true** rather than approximately
true: a draft is rarely resumable because its recorded `code_hash` was taken from the working tree
and any edit moves it, which is now a comparison with an operand — not because the gate refuses it
for a different reason that happens to coincide.

**Cost if wrong.** A dirty-tree draft is unresumable (if the gate were enforced), or a draft's record
is laundered into a citable one (if the flag were dropped). The second is the one that reaches a
paper, which is why `draft` is in `identity.json` at all.

### Decision 13 — every refusal `resume` decides is printed through one fresh credential-bearing `Collector`, never raised into `main`

**Question.** `resume` calls `_prepare_run`, which imports the entrypoint and runs a plugin
resolver — user code that can raise carrying a credential it read. `cli.main`'s
`except PublishableError` handler prints `{exc}` with **no `Collector`** and therefore no redaction
(measured by reading; H9-SCOPING C3 records the same). Which mechanism reports `resume`'s refusals?

**Answer.** One, and it is the `Collector`. Every `E-RESUME-*` and every `E-RUN-LOCKED` `resume`
itself decides is rendered through a **fresh** `Collector` whose `credentials` is the set
`_prepare_run` already resolved — never a second derivation, because a second derivation is a second
answer — and printed to stderr. Nothing `resume` decides reaches `main`'s un-redacted printer.

**Grounds, and the trap it avoids.** This is the fifth proxy in `CLAUDE.md` § Answering a question
with a proxy, in its own words: *"copying a recipe's calls without its containment."* `freeze`'s
credential wiring was cited as the precedent for `report`'s, the calls were lifted, **the `try` they
sit inside was not**, and a declared credential reached stderr verbatim. `_prepare_run` already has
this right — its roster wrapper is `except BaseException` with a fresh credential-bearing
`Collector` and `KeyboardInterrupt` re-raised fresh and argument-less — so `resume`'s containment
is that block's shape, copied **with** where it sits. The positive control is a project whose
resolver raises with a declared credential in the message, resumed, asserting `<redacted:…>` on
stderr; an undeclared credential would pass vacuously.

**Cost if wrong.** A credential in a diagnostic, in a case § Secrets & credentials explicitly
promises to redact — a leak H7c and H7b Part B have each already shipped and fixed once.

### Decision 14 — `_execute_prepared` gains one optional parameter; there is no third execution path

**Question.** How does `resume` enter phases 6–10?

**Answer.** `_execute_prepared(prepared, *, draft: bool, resumed: Resumed | None = None)`, where
`Resumed` is a frozen dataclass holding the existing run directory, the reconstituted prior results,
the per-triple attempt counts, and the replayed baseline. When it is `None`, every line behaves as it
does today. When it is not: `allocate_run_dir` is skipped, the run-start artifact writes are skipped
(they exist and are never rewritten), the plan is ordered from `sweep.yaml` and filtered to the
triples with no `completed` record, `planned` stays the **full** plan's length, the prior results are
prepended, and the baseline is threaded into the `Observer`.

**Grounds.** H9a's seam exists so that *"`run`, `draft` and (H9b) `resume` are three entries into ONE
execution path rather than three copies of it"* — its own docstring. A third function would be the
third copy, and the aggregate phase is 1,400 lines of the exact reasoning nobody should own twice.
`Prepared` is frozen on purpose — *"that is the property `resume` will rest on"* — so the overrides of
Decision 10 go through `dataclasses.replace`, not through mutation.

**This is a change to a shipped code path, and it gets H9a batch 2's treatment.** Its batch is a batch
of one, and its review is a **real-command** comparison: one config run through the console script on
a `main` worktree and on the branch, `run.yaml` equal leaf by leaf, the tree equal path by path,
`sweep.yaml`, `executions.jsonl` key by key, stdout, stderr and the exit code — with the normalization
list written **in advance** and every remaining difference attributed individually. Green tests are
not the evidence.

**Cost if wrong.** A silent behaviour change to `run` in a record every downstream command reads,
with no reader who could see it. **A normalization decided after seeing a diff is a normalization
chosen to hide it**, so the list goes into the report first and the review's job is to check it was
not tailored.

### Decision 15 — `freeze` gains the `parameters_hash` comparison, closing the standing filing rather than leaving its operand unread

**Question.** `spec-defects.md` § *a plain `parameters` edit to the run-start `config.yaml` copy
changes the cfg `freeze` probes under* names H9 as owner and hands the decision to `resume`'s design:
whether `resume`'s comparison closes it for `freeze` too, or a run-start artifact is warranted
independently.

**Answer.** The artifact is warranted, and **`freeze` must do its own comparison** — `resume`'s does
not close it. Under Decision 7 `resume` reads the *project's* config and never touches the run
directory's copy, while the filing's gap is an edit to that copy. So `freeze` computes
`parameters_hash` over the copy it already loads and refuses `E-FREEZE-CONFIG-EDITED` on a mismatch
against `identity.json`.

**An absent `identity.json` is not this fault**, and the § Errors row says so: a run directory started
by a build that predates the artifact has nothing to compare, and `freeze` behaves exactly as it does
today. Stating it in the row is what stops the next reader filing the silence as a defect.

**Grounds for building it here rather than deferring.** Declining would leave an operand with no
reader — this repository's own named defect class, and the entry's owner line is H9. No remaining
slice has `freeze` as its surface (H9c is `reproduce`, H9d is `demo`/`docs`/`list-templates`, H3c-3's
remaining 14 is cells), so *"whichever slice next touches `freeze`"* would resolve to nobody. The cost
is one code, one row, one fixture, and one disclosure line.

**Cost if wrong.** `freeze` gains a refusal for a run directory somebody edited on purpose — with a
code that names the file and the remedy. The alternative is a probe measuring under parameters the run
never adopted, which is the filing.

### Decision 16 — the bytecode-cache defect is **not** H9b's, and `resume` inherits no new exposure

**Question.** H9-SCOPING § 13's corrected H9b list puts the `discover_local` bytecode-cache fix at
H9b task 11, closing two filings. Is it H9b's?

**Answer. No — it is H9d's**, and the two records disagree. `spec-defects.md`'s own re-owning table,
**dated 2026-08-23 and recorded by H9a task 13**, routes *"`discover_local`'s bytecode cache can serve
a STALE `templates/*.py`"* to **H9d** and *"a same-size, same-second rewrite of a report override"* to
H9d as well. The later dated record wins, and two of the fault's three call sites
(`report.render_with_override`, `base_experiment.load_experiment`) are not `resume`'s surface at all.

**And `resume` inherits nothing new**, which is the substantive half rather than a jurisdictional
one: `resume` resolves its template and its entrypoint through the **same** `_prepare_run` calls `run`
and `draft` already make, so the exposure is `run`'s exposure, not a new one this slice creates. A
same-second rewrite between a crash and a resume is the same hazard as one between two `run`s.
Recorded here so H9d's design has it.

**Cost if wrong.** A resume executes against a stale template body cached in the same second. Named
in the filing, owned by H9d, and not silently inherited.

### Decision 17 — fourteen codes are minted, no exit code is, and each row is placed by its table's own scope sentence

**Question.** What does `resume` refuse, with which codes, and at which exit?

**Answer.** Thirteen `E-RESUME-*` codes plus `E-FREEZE-CONFIG-EDITED`, all `ContractError`, all
exit `1` — *"the thing you asked about is wrong"*, whose own row already names *"a `resume` whose
hashes moved."* **No exit code is minted**: `3` and `4` name `resume` already and gain their first
`resume` reader through `_execute_prepared`'s unchanged final mapping; `5` is reached by the apparatus
paths already there.

| Code | Refuses |
|---|---|
| `E-RESUME-NO-IDENTITY` | no `identity.json`, or it does not parse to an object with the five keys |
| `E-RESUME-NO-CONFIG` | `environment/repo_root.txt` absent, empty, or not a directory; or the recorded `config_path` does not resolve to a file **under** that root |
| `E-RESUME-RUN-ENDED` | the directory holds a `run.yaml` — that run ended, and its record is never modified |
| `E-RESUME-CODE-MOVED` | recomputed `code_hash` ≠ recorded |
| `E-RESUME-PARAMS-MOVED` | recomputed `parameters_hash` ≠ recorded |
| `E-RESUME-LOCKFILE-MOVED` | recomputed `uv_lock_hash` ≠ recorded, in either direction, `null` included |
| `E-RESUME-INPUT-MOVED` | `manifest_hash(fresh)` ≠ `manifest_hash(recorded)` |
| `E-RESUME-PLAN-MISSING` | no readable `sweep.yaml`, or it holds no `conditions` list |
| `E-RESUME-PLAN-MISMATCH` | re-expansion disagrees with the recorded plan on any condition's four-tuple |
| `E-RESUME-LEDGER-UNREADABLE` | a line of `executions.jsonl` is not a JSON object, or lacks `step`/`scope`/`condition`/`repeat`/`status` |
| `E-RESUME-ROWS-UNREADABLE` | a skipped triple's `units.parquet` will not decode, or its columns do not cover that line's `recorded_columns` |
| `E-RESUME-ROWS-MISSING` | a skipped triple's line names a non-empty `recorded_columns` and no `units.parquet` exists |
| `E-RESUME-ALLOCATION-STALE` | `allocation.json` will not parse, or names a unit the roster no longer holds |
| `E-RESUME-PROBES-UNREADABLE` | `replay_ledger` refuses the probe ledger, reported under `resume`'s own code |
| `E-FREEZE-CONFIG-EDITED` | Decision 15 |

**Three codes were considered and not minted.** A missing `identity.json` and a missing
`repo_root.txt` were nearly one code; they are two because the remedies differ (run again versus
restore the directory). A missing baseline is not a code at all (Decision 11). And a nonexistent
`resume` path reuses the shipped `E-IO-FAILED`, which § Exit codes already assigns to *"a `diff`
operand path that doesn't exist"* — the same question, and `diff` is the precedent.

**Every row is placed by re-reading its destination table's lead paragraph.** `E-RESUME-*` are raises
that `resume` reports through a `Collector`, so they go where `E-FREEZE-*` already sit — § Errors
`validate` reports, whose lead says *"these are the codes a **command** reports"* and whose
`E-FREEZE-*` rows are the shipped precedent for a command's own refusals. `E-RUN-LOCKED` and
`E-RUN-ID-EXHAUSTED` go to § Errors core raises (Decision 3). **The two placements are different and
that is deliberate**, and the task that writes them must quote each lead in its report — H6a's batch
4 put a row in a table whose scope did not admit it, and its review settled the question by citing a
design instead of the table.

**Cost if wrong.** Fourteen rows in the wrong table, or narrower than their codes — which is exactly
the thirteen-plus-one H9a's gate found.

---

## 3. Where this design disagrees with the scoping

Reported individually and attributed, per `CLAUDE.md`'s note that six consecutive slices reported zero
disagreements and all six were wrong. Each was found by measuring, and each measurement is named.

1. **§ 4.5's central claim is false.** *"`aggregated` survives (it is recomputed from `units.parquet`,
   which is on disk)"* — it is computed from `ExecutionResult.rows` through `collapse_repeats` and
   `attrition`, read at `cli.py`'s phase 8. So the durability hole is **four** fields, not
   `per_repeat` alone, and a resume that skipped triples would publish every interval over a fraction
   of the units. Decision 4. **This is the slice's headline correction.**
2. **The rename-as-mutex answer to Ruling W is falsified by probe**, four winners of four on trial 0,
   and so is scan-then-claim, two winners on trial 0. Decision 2's token protocol survived 60 trials
   × 5 processes with a positive control. § 0.
3. **`verify_manifest` cannot answer the resume question** — it compares the input directory against
   the manifest it is *handed*, so a resume rebuilding one would compare now against now. Named in no
   scoping finding. Decision 8.
4. **The bytecode-cache fix is H9d's, not H9b's.** § 13's corrected list says H9b task 11;
   `spec-defects.md`'s own re-owning table, dated the same day and recorded by H9a task 13, says H9d.
   Decision 16.
5. **`_execution_block` hard-codes `"attempts": 1`**, so § Resuming's *"`attempts` counts how many
   times that triple was executed"* has no code behind it at all — not merely no `resume` to exercise
   it. Named in no finding. Decision 6.
6. **`run_status`'s assert does not need changing.** § 13's task 13 asks for *"the bare assert either
   satisfied or replaced by a stated rule"*; reconstitution satisfies it, and its docstring's claim
   stays true of `resume`. Decision 6.
7. **`units.parquet` cannot be read back unambiguously without a new ledger key.** A recorded key
   colliding with a declared attribute name lands the *recorded* value under one column, so
   subtracting attributes by name would drop a real column. Named in no finding, and it is the
   proxy-substitution trap in a new currency. Decision 5.
8. **A `completed` triple can legitimately have no `units.parquet`** — `finalize` writes it only
   `if self._rows`, so a scalar-only repeat step completes and writes nothing. The crash fixture of
   § 4.1 has one recording step and therefore **cannot distinguish** that from a missing file;
   Fixture B fixes the project shape rather than the assertion.
9. **`resume`'s refusals need one reporting mechanism, and the scoping names none.** C3 records that
   `main`'s handler uses no `Collector`; it does not draw the consequence for a command that runs a
   resolver. Decision 13.
10. **`lock`'s third key has a job, and it is not liveness.** § 4.3 measures the two written keys;
    this design says what the third is for (the diagnostic) and states in writing that the liveness
    test does not consult it, so PID reuse refuses. Decision 2.
11. **A crashed run leaves no `latest` pointer either** — `point_latest` runs after `run.yaml`.
    Measured on the crash fixture; § 4.1's tree does not name the absence, and it matters because
    § Resuming's own invocation example is `resume …/latest`.
12. **`identity.json` moves three shipped assertions, one of which has editor NONE.** § 13 names no
    pin consequence at all. § The guard pin.
13. **`replay_ledger` needs a code parameter, not a rename.** C1 offers *"the code is renamed … or
    `resume` gets its own"* and leaves it open; renaming a shipped diagnostic breaks a grep, so the
    default-valued parameter is the answer that keeps `freeze` byte-identical. Decision 11.
14. **The scoping's own H9b count is 15 and this plan is 18.** Its closing note predicts exactly
    that, and Decision 4 is where three of the extra tasks come from.

---

## 4. What this slice refuses to build

The scoping's § What H9 must not fold in is the starting list; every row was re-checked at `1daf3b4`.

| Not H9b's | Where it goes | Verified |
|---|---|---|
| Folds and holdouts **inside cells** — the phase hoist of `_resolved_group_axes`/`arm_members`, the cell decomposition, `fold_basis` per cell, `sweep.yaml`'s per-cell `partitions` | **H3c-3's remaining 14**, tasks 2–17. H9b reads `allocation.json` and `sweep.yaml`'s `partitions`; it does not move either resolution | Both calls still inside `_prepare_run`; Decision 10 overrides their *results*, never their position |
| `E-DATA-HOLDOUT-CELLS` / `E-REPL-FOLD-CELLS` retirement | **H3c-3** | Unchanged |
| `reproduce`, the four lockfile questions, `apparatus.expected.json`, the H6a-boundary verdict | **H9c** | `identity.json` records `uv_lock_hash` for a *comparison against the same machine*; it decides nothing about a clone |
| `demo`, `docs`, `list-templates`, the managed regions | **H9d** | `scaffold.README` still has two regions; no parser exists |
| The `discover_local`/`report`/`base_experiment` bytecode-cache fix | **H9d**, per `spec-defects.md`'s dated re-owning table. Decision 16 | `resume` inherits `run`'s exposure and creates none |
| `E-INPUT-CHANGED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS` rows | **Unassigned, with the reason** — the manifest path and `generators/`/`scaffold.py` are not H9b's surface | Decision 8 mints its own code rather than borrowing `E-INPUT-CHANGED` |
| `max_failed_fraction`'s truncation status semantics | **Unassigned**, filed by H7d Part B with a written justification in a shipped test's docstring. `resume` re-enters the same loop and **must not weaken that pin** | Decision 6; named as a task constraint |
| `BaseTemplate.field_convention`'s missing reader | **Unassigned.** H9b creates no new one — every `identity.json` key has a reader, and Decision 1 refuses `input_manifest_hash` for exactly that reason | Re-grepped: three hits in `src/`, none a reader |
| `report_by` under `resample` keeping a `t_over_units` interval | **Unassigned**, filed against H4, live on seven configs | `resume` computes the same construction `run` does |
| `dry-run`'s sweep header reading as a false equation | **Unassigned**, filed by H9a task 12. H9b adds a line to the fixed-file list and does not touch the header | The header's format string is not edited |
| The 195 `command_run` prose references | **Unassigned**, filed by H9a task 13, which predicts H9b makes the residue grow. H9b adds the third caller of `_prepare_run` and **re-reads that entry** rather than re-deriving the count; any `command_run` claim it cannot leave standing is **deleted**, never rewritten | The entry's own instruction |
| A marker for the hash definition in `run.yaml`; a fourth hash; a `provenance` key naming core's version; a `gpu` key | **Refused by ruling** (H6a Ruling C, H6a Decision 12 / Ruling E, H6b Decision 5). `identity.json` is not a `provenance` key and mints no hash — it records three figures `run.yaml` already holds | H9b adds no `provenance` sub-key |
| Widening `E-CODE-DIRTY`'s pathspec | **Declined and unassigned** (H6b Decision 12). Decision 12 uses the same `allow_dirty` parameter H9a introduced and touches `provenance.py` not at all | The `resume` task may not touch `provenance.py`, and its diff must show `git_provenance` unchanged |
| A retry of a failed execution, or of a unit | **Refused by specification.** § Resuming: automatic retry *"would be a behavior nothing in the config describes"*, and retrying a unit stays in the step's own loop | `resume` re-executes a triple with no `completed` record and never a second time within one invocation |
| Amending an earlier ledger record | **Refused by specification** — append-only. A resumed attempt appends its own record, which is where `attempts` comes from | Decision 6 |

---

## 5. Is this additive? — the disclosure

**No.** Six things move, and **item 3 is the one a reader would find by diffing behaviour rather than
by reading this list** — the same shape as H9a's item 3, whose disclosure was wrong in three records
until the gate measured it.

**1. `run`, `draft` and `resume` write a new run-start artifact.** `<run_dir>/identity.json`, five
keys, inside the lock, before `sweep.yaml`. Two shipped assertions move with it (§ The guard pin,
arms B and D).

**2. `executions.jsonl`'s line gains two keys**, `returned` and `recorded_columns`. Ten keys where
eight are written today. One shipped assertion moves (arm C), **and it has editor NONE at HEAD** — the
design re-authorizes it in Decision 3 of § The guard pin, with the post-edit set written in advance.

**3. `dry-run`'s printed output changes for every user.** `_DRY_RUN_FIXED_FILES` gains
`identity.json`, so `dry-run` prints **8** fixed files where it prints 7, and the shipped assertion
`assert "and 7 fixed files in that directory:" in out` becomes `8`. `dry-run` is a command a user runs
before spending money; its transcript is the thing they read. **This item is not "a test literal
moves"** — it is a shipped command's output, and it is listed third because it is the item a reviewer
finds by running rather than by reading.

**4. `run.yaml`'s `attempts` becomes a count rather than a literal.** For a plain `run` the value is
unchanged — every triple has exactly one ledger record — and that equality is **measured leaf by leaf
against `main`**, not asserted. `assemble_run_yaml` gains one optional argument defaulting to `None`,
whose `None` branch is byte-identical to today.

**5. `publishable resume` changes what it answers, in four shapes, three of which are measured at
HEAD and one of which is owed a measurement by its own task.** Today all four print the unbuilt
diagnostic and exit `2` (measured through the real console script):

| Invocation | At HEAD | After H9b |
|---|---|---|
| `resume` | exit 2, unbuilt diagnostic | exit 2, `` `resume` takes exactly one path and no flags`` — the shared arity arm |
| `resume a b` | exit 2, unbuilt diagnostic | exit 2, the same arity line |
| `resume --json` | exit 2, unbuilt diagnostic | exit 2, the same line, via the leading-`-` half |
| `resume new` | exit 2, unbuilt diagnostic | **exit 2 → 1**, and the line is `resume`'s own refusal for a path that is not a run directory. `"new"` is a single token, so `rest == ["new"]` never trips the arity arm at all and the call dispatches into `command_resume` |

The last row is **derived by reading `_dispatch`** — the built branches precede the
`NOT_BUILT_COMMANDS` lookups, and the two-token arm is evaluated first — and it is exactly the row
H9a got wrong for `draft new`. **The task that dispatches `resume` must measure all four through the
real console script and correct this table in its report if any of the four differs.** A wrong
disclosure is worse than none.

**6. `freeze` gains a refusal**, `E-FREEZE-CONFIG-EDITED`, for a run directory whose `config.yaml`
copy was edited after run start (Decision 15). An absent `identity.json` leaves `freeze` behaving
exactly as today.

**What does not move, stated so the negative is on the record.** No `run.yaml` key is added, removed
or reordered — `draft` and `attempts` already exist. No `provenance` sub-key changes. No hash
definition changes. `schema_version` is not bumped. `RunLock.__enter__`'s claim is byte-unchanged apart
from the third key it writes into its own JSON payload. `git_provenance` is byte-unchanged. `dry-run`
takes no lock and creates nothing, still. No exit code is minted.

---

## 6. Does § Executability move?

**No, and it is derived rather than repeated.** The four-row table in
[`docs/feasibility-llm-growth-studies.md`](../../feasibility-llm-growth-studies.md) § Executability on
this build is repeated **character for character** from the H8a entry, as every entry since has done,
and **no fifth number is minted.**

The derivation, row by row:

- **Row 1, transplantable configs validating with zero errors — 8 of 8.** `resume` runs at no
  `validate` and from no step, and Decision 14's `resumed=None` branch is behaviour-preserving, so
  `validate`'s answer for these configs is byte-identical.
- **Row 2, blocked on `io.reuse_from` — 0.** Untouched; H8a settled it and `resume` reads no upstream
  it does not inherit.
- **Row 3, meet the `report_by`-under-`resample` gap — 7.** A construction chosen inside
  `summarize_step`, in phase 8, which a resumed run reaches identically.
- **Row 4, free of every core-side dependency this analysis can name — 1.** `resume` requires a
  crashed run directory, which is a property of an operator's history and not of a config; none of the
  nine configs declares an `apparatus_probe`, a `study`, a `fold` or a group axis.

**H9b therefore unblocks ZERO configs**, and the reason is structural: `resume` is a second entry into
a sequence these configs already reach or do not. One dated entry, the table repeated unchanged.

---

## 7. The guard pin

Captured in **batch 1, before any code moves.** Every arm names a sole authorized editor or an
explicit **NONE**, and every authorized post-edit state is written **now** — H6a captured against a
superseded signature and forced an unauthorized edit; H6b and H9a captured forward and their edits
matched the advance spec byte for byte. **An implementer may not self-authorize an arm edit. The route
is a controller ruling, and leaving the branch red is correct** — H9a task 2 did exactly that and was
right to.

| Arm | What it holds | Authorized editor |
|---|---|---|
| **A** | **A crash-and-resume round trip equals a straight-through run**, leaf by leaf: the same config run to completion under `run`, and run again with a crash at its last execution followed by `resume`, with the two `run.yaml`s compared over every leaf in order against a normalization list fixed in advance (`at`/`started_at`/`wall_seconds`, `run_id` and everything derived from it, absolute paths, `hostname`, the three hashes, and `attempts`). **This is the arm Decision 4 exists for**, and no per-key assertion substitutes for it: `_gather_repeats` builds its column order from row iteration order and `summarize_step` derives a metric's column order from that, so a parquet round trip can move `run.yaml`'s column order with every value correct | **NONE** |
| **B** | `test_h8b_arm_a_the_run_directorys_root` — the run directory's sorted root list, **editor NONE at HEAD and re-authorized here**. Post-edit list, written now: `['conditions', 'config.yaml', 'environment', 'executions.jsonl', 'identity.json', 'manifest', 'run.yaml', 'sweep.yaml']` — one entry appended, sorted, nothing reordered | **The `identity.json` task only** (plan task 4) |
| **C** | `test_h9a_arm_d_the_executions_jsonl_line_key_set` — **SOLE AUTHORIZED EDITOR: NONE at HEAD, and Decision 5 re-authorizes it.** Post-edit set, written now: `{step, scope, condition, repeat, status, started_at, wall_seconds, error, returned, recorded_columns}` — two keys added, none removed | **The ledger task only** (plan task 6) |
| **D** | `dry-run`'s fixed-file count — the shipped `assert "and 7 fixed files in that directory:" in out`. Post-edit state, written now: `8`. The set-to-set comparison beside it against a real run's tree is **self-maintaining and must not be edited** | **The `identity.json` task only** (plan task 4) |
| **E** | `test_reference_cli_tables_are_parsed_at_all`'s shipped `assert ("resume", "NOT BUILT") in tables["Command"]`. Post-edit state, written now: that line becomes `("resume", "built")` **and** a line `assert ("reproduce", "NOT BUILT") in tables["Command"]` is added, so the table keeps a marked row-presence probe. The `set(NOT_BUILT_COMMANDS)` equalities are **self-maintaining and must not be edited** | **The dispatch task only** (plan task 15) |
| **F** | H9a arm A and arm B — a completed `run`'s whole `run.yaml` leaf by leaf and its full stdout line by line — **cited, not re-captured**, and they are what Decision 14's behaviour-preservation claim is measured against. Re-capturing would recreate H8a's *same list pinned twice* | **NONE** |
| **G** | **The takeover's mutual exclusion, deterministically.** Two threads racing one dead-holder run directory with a `threading.Barrier` released **between the liveness verdict and the lock replacement**, asserting exactly one holder and one `E-RUN-LOCKED`. Deterministic on purpose: the five-process probe of § 0 is the discovery instrument and is cited in the report, not used as the pin — *verify by probe, then pin by mutation* | **NONE** |
| **H** | Already pinned elsewhere and **not re-captured**: H8b arm B (`environment/`'s contents — `identity.json` is not under it), H8a arms A and B (`run.yaml`'s and `provenance`'s key lists), H8c task 17 arm A (the record's field-level shape), `sweep.yaml`'s key list, and H9a arms C and E (the four exit codes and the four early exits) | **NONE.** Cited so a reviewer does not read the absence as missing coverage |

**Every arm must be proven able to fail** before the batch is reviewed, by a mutation in the
**production** code — not by reading. And **proving an arm cannot move is not proof the line is
pinned**: an arm offered as evidence that an edit is safe *because it cannot see the edit* is two
opposite facts wearing one sentence. **Report every mutation count against the full suite**, and say
so — nine of the last four slices' miscounts were single-test-scoped numbers reported as suite-wide.

---

## 8. Fixtures as claims

Every literal is computed, and the method is named. A fixture whose numbers agree with the bug is
this repo's most frequent single defect.

| Fixture | The claim | How every literal is obtained, and why it can fail |
|---|---|---|
| **A** — the crashed run directory | A run directory in exactly the state `resume` exists for | **Built, not synthesized, and the recipe is deterministic**: a scaffolded project outside the repository, 2 conditions × 4 seed repeats over 6 units, whose repeat step increments a counter file outside `input_dir` and calls `os._exit(9)` when it reaches a fixed value. Measured twice; both times the directory held `config.yaml`, `environment/{pyproject.toml,repo_root.txt}`, `executions.jsonl`, `lock`, `manifest/input.json`, `sweep.yaml`, two `completed` ledger lines, one step directory with no `units.parquet` — and **no `run.yaml` and no `latest`**. Determinism comes from the counter file, not from timing; `os._exit` is what leaves the lock behind, which is the state Decision 2 is about |
| **B** — the round-trip project | Arm A's equality, over a project shaped to distinguish the readings | **Two repeat-scope steps**: one recording (so `units.parquet` exists and `recorded_columns` is non-empty) and one **scalar-only** (so a `completed` triple legitimately has no `units.parquet`). The crash fixture of the scoping's § 4.1 had one recording step and therefore **cannot tell "recorded nothing" from "file missing"** — the two readings Decision 5's empty list exists to separate. A declared attribute is also carried, **with one recorded key deliberately colliding with its name**, so the attribute subtraction is exercised against the case that breaks a by-name rule |
| **C** — a `resume` that completes | `status: completed`, exit `0`, `attempts` `2` for the crashed triple and `1` for its neighbours | The `attempts` values are **counted from the ledger the run itself wrote**, never from the plan's arithmetic — the count is the thing under test |
| **D** — a `resume` whose status is `partial` **because of the previous attempt** | § What status means' `partial` folds a failure recorded by an attempt this invocation never ran | The failure is produced by a step that raises on its first attempt and succeeds on its second, keyed off the same counter file. **The one shape no direct call can build**, and the reason this is an end-to-end fixture: `run_status` over a hand-built list proves nothing about whether the reconstituted result reached it |
| **E** — each of the fourteen refusals | One fixture per code, each perturbing exactly one thing from Fixture A | Each is built by **mutating the crashed directory**, one file at a time: `identity.json` removed; a hash key rewritten; `sweep.yaml` removed; a condition's `values` edited; a `units.parquet` truncated; a `recorded_columns` naming a column the file lacks; an `allocation.json` naming an absent unit; a `run.yaml` dropped in. Each asserts the code **and** that nothing executed — the step's counter file must not have advanced, which is a positive assertion rather than an absence |
| **F** — the live lock | `resume` against a directory whose lock holder **is** this process refuses `E-RUN-LOCKED` and executes nothing | The holder is the test process itself, so `os.kill(pid, 0)` genuinely succeeds. A fabricated pid would make the fixture agree with a bug that always reads *dead* |
| **G** — the undecidable lock | Each of the five *cannot tell* states refuses | Five sub-fixtures: a `host` that is not this machine's, non-JSON bytes, a JSON array, a missing `pid`, a `pid` of the wrong type. **A control asserting only absences passes identically if nothing ran**, so each also asserts the counter file did not advance |
| **H** — the drawn allocation | `allocation.json` is read rather than re-drawn | A **drawn** axis (`method: random`), where a second draw would differ — and the fixture asserts the resumed memberships equal the recorded ones, not merely that the file was opened. A `by_attribute` axis would make correct and buggy readings coincide, which is testing one reading twice |
| **I** — the apparatus baseline | A resumed execution is gated against the **original** run's first-answered facts | A project-local probe whose answers are read from a file the fixture rewrites **between** the crash and the resume, so the original baseline and the resume's own first probe **differ**. Without that difference the mutation removing the replay is blind, which is exactly how H9a's Fixture Y failed |
| **J** — the credential positive control | A resolver raising with a **declared** credential in its message prints `<redacted:…>` at `resume` | The credential is declared through `Param(requires_env=)` and set in the environment, so the redaction has a real value set to match against — an undeclared one would pass vacuously |
| **K** — the `freeze` comparison | `freeze` refuses `E-FREEZE-CONFIG-EDITED` after a plain `parameters` edit to the copy, and behaves as today when `identity.json` is absent | The edit is to `parameters` **only**, so `E-FREEZE-PLAN-MISMATCH` cannot fire and the new check is the only thing that can refuse. The absent-artifact arm is the negative control, and it asserts `freeze`'s **full** shipped output rather than only its exit code |

---

## 9. Mutations

Each is named with the assertion that catches it, and **each was checked in advance for two branches
that can differ** — a mutation whose branches cannot differ is a claim like any other.

| Mutation | Caught by | Two branches differ? |
|---|---|---|
| Drop the reconstituted results from `resume`'s `results` list | Fixture C via arm A | **Yes** — Fixture B has 2 conditions × 4 repeats and the crash is at execution 3, so five triples are reconstituted and every interval and every `n` moves |
| Reconstitute `status`/`started_at` but not `rows` | Arm A | Yes — `recording_steps` drops the step, so the whole `aggregated` block for those conditions disappears |
| Subtract attribute columns **by name** rather than by `recorded_columns` | Fixture B | Yes — B carries a recorded key colliding with a declared attribute name, so the by-name rule loses a real column while the structural rule keeps it |
| Treat a missing `units.parquet` as `E-RESUME-ROWS-MISSING` unconditionally | Fixture B's scalar-only step | Yes — that step legitimately writes none, so the unconditional reading refuses a directory the correct reading resumes |
| Write `returned` without `summary_values` | Fixture C, extended with a `summary` step returning an `Estimate` | Yes — a raw `Estimate` is not JSON-serializable, so the ledger write raises |
| Keep `"attempts": 1` as a literal | Fixture C | Yes — C's crashed triple ran twice |
| Compare `manifest_hash(fresh)` against itself instead of the recorded file | Fixture E's moved-input arm | Yes — the arm rewrites a file under `input_dir` between the crash and the resume, so the two digests differ |
| Order the plan by re-realizing the shuffle instead of reading `execution_order` | A `order: randomized` arm of Fixture C, asserting the resumed ledger's order continues `sweep.yaml`'s | Yes — the arm's `sweep.yaml` is edited to a recorded order the seed does not reproduce, so the two answers differ |
| Skip the `allocation.json` override | Fixture H | Yes — H's axis is drawn and the fixture edits the recorded memberships away from what a second draw gives |
| Skip the baseline replay and let the resume's first probe set the baseline | Fixture I | Yes — I's probe answers differ across the crash, so the replayed gate refuses and the un-replayed one proceeds |
| Delete the takeover token's exclusive create | Arm G | **Yes, and measured**: the five-process probe produced two winners by trial 22 with the token removed, and arm G's barrier makes the same interleaving deterministic |
| Treat an unparseable `lock` as *dead* | Fixture G | Yes — G's non-JSON arm resumes under the mutation and refuses without it |
| Consult `started_at` in the liveness test | **Named blind in advance** — no fixture makes a `started_at`-consulting test disagree with a `pid`-only one, because that would need a genuinely recycled pid, which cannot be forced | **No.** Owed a replacement: the non-use is asserted **structurally** — a test that constructs a lock whose `started_at` is absent entirely and whose pid is dead, and asserts the takeover proceeds. A liveness test that read `started_at` would have to refuse it |
| Report a `resume` refusal by raising into `main` instead of through a `Collector` | Fixture J | Yes — J's message carries a declared credential, so the two paths print the value and `<redacted:…>` |
| Replace `isinstance(prepared, Prepared)` at `command_resume`'s call site with a truthiness test | **Named blind in advance** — `Prepared` has no falsy instance and phases 1–5 never return `EXIT_OK`, so `0` is the only `int` the swap would mis-handle | **No.** Owed a replacement: the rule is stated once in `command_resume`'s docstring, `mypy` is the enforcer, and H9a arm E pins the four early-exit codes end to end. **The same mutation was named blind by H9a and the reason is unchanged** — it is repeated rather than re-derived |

---

## 10. Batching

**Eighteen tasks in eight batches, every batch reviewed.** The count is what the tasks came to, not a
figure aimed at the scoping's 15 — the scoping predicts a plan exceeds its own count, and merging
tasks to hit a number is the failure mode that prediction is about.

| Batch | Tasks | Why together | Review |
|---:|---|---|---|
| **1** | 1 | The guard pin, before anything moves — including the two re-authorizations | Every arm proven able to fail, by a **full-suite** mutation, with the count reported as such |
| **2** | 2, 3, 4 | **The run-start artifact — the batch that changes `run`'s artifacts.** `identity.json`'s content, its write site, and the three shipped assertions it moves | **A real-command review**: `run` through the console script on a `main` worktree and on the branch, `run.yaml` leaf by leaf, the tree path by path, `dry-run`'s transcript line by line, normalization list written in advance, every remaining difference attributed |
| **3** | 5, 6, 7 | The ledger's two new keys, `attempts` from the ledger, and the `Resumed` value object — one question, what a run makes durable | The arm C edit against its advance spec; the `run`-side equality re-measured |
| **4** | 8, 9 | **The `_execute_prepared` change, and task 8 is alone with it in spirit** — reconstitution reads what task 9's branch consumes | **A second real-command review**, on the `resumed=None` path: green tests are not the evidence |
| **5** | 10, 11, 12 | `resume`'s own reads — `sweep.yaml`'s order, `allocation.json`, the manifest comparison | The drawn-axis fixture; the recorded-order mutation |
| **6** | 13, 14 | The apparatus baseline and the lock takeover — the two places `resume` inherits a mechanism named for another command | Arm G; the credential positive control |
| **7** | 15, 16 | `resume` dispatched, and the fourteen refusals wired | **All four invocation shapes measured through the real console script**, and item 5 of the disclosure corrected if any differs |
| **8** | 17, 18 | The documents, the records, `spec-defects.md`, `CLAUDE.md`, and both consistency passes | **The batch with no review is where the findings will be**; this one is reviewed, and three of one gate's four Majors lived in exactly such a task |

**Batches 2 and 4 each change a shipped code path or a shipped artifact, and each is reviewed against
a real command rather than against the suite.** That is the split this project has taken twice (H8b
Decision 7, H7d Part B) and the one H9a's batch 2 established the method for.

---

## Appendix — corrections appended 2026-08-23, before dispatch

Appended rather than edited, so the dated measurements above stay as they were made. Three items; the
first replaces a **ground**, not a decision.

**A1. Decision 5's *"serializable by invariant"* is wrong as written, and the encoding rule is now
named.** Measured: `json.dumps({'r': float('nan')})` emits `{"r": NaN}`, and `inf`/`-inf` emit
`Infinity`/`-Infinity` — none of them valid RFC 8259 — while `coerce_scalars({'r': float('nan')},
'step', scope='repeat')` passes the value through unchanged, so a step returning a non-finite float is
reachable and legal and `run.yaml` (YAML) already records it. **This is the second exception to the
flat-mapping-of-scalars invariant, and `Estimate` was the first** — which Decision 5 caught only
because it read `summary_values` rather than trusting the invariant.

**The rule: the ledger keeps `json.dumps`' shipped default (`allow_nan=True`) and the document says
so.** `executions.jsonl` is written and read back by the same `json` module — measured:
`json.loads('{"r": NaN}')` returns `nan` — so the round trip is **exact**, which is what guard-pin arm
A's leaf equality requires. The two alternatives were weighed and rejected: `allow_nan=False` would
**fail a completed execution** over a value `run.yaml` accepts, which is the wrong direction; encoding
non-finite as `null` would make a resumed `per_repeat` differ from a straight-through one, breaking
arm A and losing the distinction between `nan` and a genuinely-null value. **The non-promise is
stated rather than left silent**: task 17 records in § `executions.jsonl` that its lines are
Python-`json`-compatible rather than strict JSON, and why.

**A2. The disclosure has a seventh item.** `apparatus.replay_ledger` gains a code parameter
(Decision 11, plan correction 18). It is additive and defaulted, so `freeze` is byte-identical — and
that is a claim about a shipped function's signature, so it belongs in the enumeration rather than
under a threshold. **Measured by task 13, not asserted here.** § Is this additive? is an enumeration
and an incomplete one is the same class of fault as a wrong one.

**A3. Guard-pin arm A is half live from batch 1 and half `xfail` until task 9, and a reviewer must not
read the whole arm as coverage.** The `run` half — the straight-through golden — is live from batch 1
and is what **batches 2 and 3 are held to**, alongside task 4's real-command review. The resume half
is `xfail(strict=True)` naming task 9. Arm G is `xfail(strict=True)` in full until task 14, and task
4's real-command review is the actual guard over that window.

---

## Correction, 2026-08-23, from batch 1 — the guard pin's editor parenthetical named the wrong task

**§ The guard pin gives arms B and D the editor parenthetical "H9b task 4". That is wrong and this
replaces it: their editor is the task that WRITES `identity.json`, which is plan task 3.** Plan task 4 is
the comparison that may touch nothing, and plan task 3's own text already grants the authority — so the
design's parenthetical contradicts the plan while the two sibling parentheticals (arm C → task 6, arm E →
task 15) are correct, which is what makes this one a slip rather than a scheme.

**Recorded rather than edited because a wrong editor name is the failure mode the device exists to
prevent.** An arm names its sole authorized editor *in advance* so that any other task touching it is
visibly out of order; an arm naming a task that cannot legally edit it invites the next implementer either
to stop on a false blocker or to self-authorize on the grounds that the name must be a typo. **Batch 1 did
neither** — it wrote clauses naming the task descriptively **and** stating the discrepancy, which is the
third option and the right one.
