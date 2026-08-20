# H8a batch 3 (tasks 3, 5) — review

Reviewed at `db41b5a` on branch `h8a-lineage`. **Every claim below marked *ran* was produced by
executing something in this session; claims marked *read* were not.** Mutations were applied by
editing the file, reverted by copying a pre-mutation copy back, and each revert confirmed by
`diff -q` against that copy plus a re-run. `git checkout --` was never used. Tree left clean.

## Verdicts

- **Spec compliance: PASS with one Major, which does not block the merge** — every property the batch was asked to hold holds when
  measured by running: Decision 1's `latest` asymmetry is alive, the containment fix does not
  overshoot, Decision 2's step-facing surface gains one method and zero readable fields, Decision 9's
  `ResolverIO` still has no `reuse_from`, and Decision 10 holds through a real two-run `run`. The
  Major is Decision 6's own cache guarantee — *"one answer per run … an upstream edited mid-run
  cannot give two answers inside one record"* — which the absolute locator form does **not** provide,
  while the method's docstring asserts it does. **It does not hold the batch**: task 3's brief
  prescribed *"a per-`run_id` record cache"* and that is literally what shipped, and Decision 6's
  guarantee is owed where the record is assembled — so the **false docstring clause at
  `lineage.py:302` is this batch's one-line fix**, and the guarantee itself carries to tasks 6 and 7
  **by name**, with the two pins named in the finding.
- **Task quality: PASS** — mutations were real, the placement move is right for reasons beyond the
  mutation, and the batch's own two Concerns were honest (one of them is Major 1 below, correctly
  smelled and mis-diagnosed as a missing pin). Deductions: one Fixture N arm cannot fail, and the
  closed filing claims a pin two named tests do not provide.

## Gates (all *ran*, foreground, after clearing `__pycache__` and `pytest-of-*`)

`uv run ruff check .` → All checks passed. `uv run ruff format --check .` → 84 files already
formatted. `uv run mypy` → no issues in **47 source files**. `uv run pytest` → **2494 passed, 1
skipped, 2 xfailed** (133 s). Exactly the expected literals.

---

## Findings

### Major 1 — Decision 6's "one answer per run" does not hold for the absolute locator form, and `resolve`'s docstring claims it does

`src/publishable/lineage.py:301-311` (`UpstreamResolver.resolve`; the docstring at 302-303, the
cache write at 310).

The cache is consulted **only** on the non-absolute branch (`if not path.is_absolute():`), so every
absolute-locator call re-reads `run.yaml`. **Verified by running** (counter monkeypatched over
`lineage.read_run_record`):

- three identical **absolute** locators → **3** `read_run_record` calls
- three identical **relative** locators → **1**
- absolute then relative for the same run → 1

And the consequence Decision 6 names explicitly, also **verified by running**: with one resolver, an
absolute `resolve(...)`, an edit to the upstream's `run.yaml` between the calls, and a second
identical absolute `resolve(...)` returned `code_hash` `AAAA` then `BBBB` — two answers about one
upstream inside one run. The relative form returned `AAAA` both times.

Decision 6 (design, § 6): *"The upstream's `code_hash` and `parameters_hash` are read from its record
once per `run_id` and cached, so N reads from one upstream do one record read. **One answer per
run** … a cache is also why an upstream edited mid-run cannot give two answers inside one record."*
The docstring at 302 states *"reading `run.yaml` at most once per distinct upstream run"* — false as
written, which is `CLAUDE.md`'s most-repeated habit (*a comment claiming a guarantee the code does not
provide*). The absolute form is the form § Lineage's own worked example uses (a locator in a
parameter, `cfg.parameters.program.upstream_run`), so this is not the exotic branch.

The batch's Concern 2 named the read count and framed it as *"no fixture pins a read-count
property."* It is not a missing pin: it is a guarantee on the books that the code does not keep. The
shape that keeps it is a locator→run_id map beside the run_id→record map, so both forms hit one read;
prefer that to deleting the docstring clause, since Decision 6 owes the property to task 7's record.

### Minor 1 — Fixture N's absolute-`name` arm cannot fail

`tests/test_artifacts.py:1757-1800`
(`test_reuse_from_name_containment_refuses_traversal_absolute_path_and_symlink_escape`), against
`src/publishable/artifacts.py:951`.

**Verified by mutation:** deleting `Path(name).is_absolute() or` from `_contained` only (leaving the
shipped `_resolve` at 697 untouched) leaves **all 7 `reuse_from` tests green**. The arm's target,
`str(secret)`, sits outside the step directory, so the `startswith` half already refuses it — the
*assertion implied by another in the same test* shape. The clause is not dead: **verified by running**
that an absolute `name` pointing *inside* the step directory (`str(step_dir / "out.json")`) is
refused with `E-UPSTREAM-NAME` under the shipped code and would be **read** under the mutant. That is
the config no fixture instantiates. Task 12 wires the same helper into two shipped readers, so the
arm is worth making discriminating before it is relied on twice more.

The other two arms do each discriminate on their own, **verified by two separate mutations**:
dropping `_contained` fails at the `..` arm (line 1779), and replacing `resolve()` with a lexical
`os.path.normpath` — which still catches `..` and not symlinks — fails at the symlink arm (line 1794).

### Minor 2 — the closed filing claims a pin its two named tests do not provide

`docs/superpowers/spec-defects.md:7357-7371`.

The CLOSED preamble says the fix *"also closes 'the second half of the same finding' … the relative
form now returns a resolved path"* and then names two tests as the pin. **Verified by mutation:**
keeping the containment check on a resolved probe but returning the **unresolved** path

```python
probe = (output_dir / locator).resolve()
resolved = output_dir / locator
if resolves_inside_repo(probe, repo_root): ...
```

leaves `tests/test_lineage.py` and `tests/test_artifacts.py` **142 passed** — neither named test sees
the difference, because both compare against `(output_dir / run_id).resolve()` and `tmp_path` carries
no symlink component. The containment half **is** pinned (see below); the resolved-return half is
pinned by nothing. *Reading a probe as a pin*, in a filing rather than in a comment.

### Minor 3 — a warm cache lets a **relative** locator resolve a run that is not under `output_dir`

`src/publishable/lineage.py:304-308`.

Because the relative branch returns a cache hit **before** `resolve_run` runs, neither
`<output_dir>/<locator>` nor the containment check nor the run_id comparison is reached once
something has cached that run_id. **Verified by running**, one resolver, upstream at
`<root>/elsewhere/whatever` with `run_id: run_…_eeeeeee` and an `output_dir` that does not contain
it:

- cold: `resolve("run_…_eeeeeee")` → `E-UPSTREAM-RECORD-MISSING` (correct)
- warm (after `resolve("<abs path to elsewhere/whatever>")`): → **OK**, returning
  `…/elsewhere/whatever`, which is **not** under `output_dir`

Decision 1's first bullet and `reference.md` § Lineage both say a bare `run_id` resolves to
`<output_dir>/<run_id>/`, *"under this config's `output_dir`"*. With a warm cache it does not, and
the same two call sites in the other order give different outcomes (success vs. a failed execution) —
the *"a fact should not be re-computable to a different answer"* argument Decision 6 makes about
insertion order, one level down.

Second, weaker face, also **ran**: an upstream whose own record says `run_id: latest`, cached through
an absolute call, makes `resolve("latest")` succeed — Decision 1's asymmetry dying through the cache
rather than through the comparison batch 2 protected. Core never writes such a record, so this face
is contrived; the `output_dir` face needs only a legal config.

**Why Minor and not Major.** No artifact is wrong: the run returned is one the config named
absolutely on an earlier call, where it passed containment — the warm path is strictly more permissive
about a run already validated, and bypasses no refusal that was not already satisfied. The
order-dependence needs two call sites in different steps addressing one upstream through different
forms, and step order is fixed within a run (`order: randomized` shuffles condition×repeat pairs, not
steps), so it is not reachable by a shuffle. The same locator-keyed cache that closes Major 1 closes
this: consult and write the cache under the **locator as given**, keeping a run_id key only as a
second map.

---

## What I verified holds (each *ran*)

**Attack 1 — the `latest` asymmetry survived the containment widening.** All four arms in one
process, plus batch 2's converse:

| Arm | Result |
|---|---|
| relative `latest` | `E-UPSTREAM-RUNID-MISMATCH` |
| absolute `<output_dir>/latest` | reads, `run_id` from the record |
| relative `run_id` where `<output_dir>/<run_id>` symlinks into a `git init`'d repo | `E-UPSTREAM-REPO-CONTAINED` |
| absolute path into that repo | `E-UPSTREAM-REPO-CONTAINED` |
| ordinary subdirectory of `output_dir`, relative form | reads |

The asymmetry survives **because only the path is resolved** — `record.get("run_id") != locator`
still compares the locator **as given** (`lineage.py:151`), which is the comparison correction 2
prescribes. **The reorder does not mask the loss:** containment now precedes `read_run_record` on the
relative branch, and I checked what that hides by building an `output_dir` *inside* the repo, where
`resolve_run("latest")` returns `E-UPSTREAM-REPO-CONTAINED` rather than the mismatch. That state is
unreachable for a real config (`output_dir` may never resolve inside the repo, checked at generate,
validate and run), so in every reachable state the mismatch arm is still the one that fires — which
the first row above shows directly.

**Attack 2 — `io.reuse_from` end to end, on my own two-run project.** A throwaway
`tests/test_zz_review_b3.py` (deleted afterwards; the tree is clean) scaffolded one project, ran it
once with a `summary` step publishing `programs/a.json` and `programs/gpt-4.1__seed29.json`, then
added three `repeat` steps, committed, and ran `main(["run", cfg])` a **second time** into the same
`output_dir`. Results:

- all three locator forms read the real upstream artifact from inside a real execution:
  `{"rel": {"program": "a"}, "abs": {"program": "b"}, "latest": {"program": "a"}}` — the bare
  `run_id`, an absolute run directory, and `<output_dir>/latest` (which still points at the upstream
  while the downstream is executing).
- Decision 10 holds: the failing step's ledger line is
  `E-UPSTREAM-ARTIFACT-MISSING ArtifactError: …` with `status: failed`, **the next step still
  completed**, the `summary` step still ran, `run.yaml` exists with `status: partial`, exit `3`.
- what survives: 5 `executions.jsonl` lines (step × the one condition/repeat pair `sweep.yaml`
  records in `execution_order`), `run.yaml`'s top-level key list unchanged (11 keys), `provenance`'s
  12 keys unchanged with **`upstream` absent** (correct — task 7's), and `<output_dir>/latest`
  repointed to the downstream run after it finished.

Also **ran**, direct-call sweep of the whole family through `io.reuse_from`, confirming every code
routes and each exception class matches correction 5: `ok`; `E-UPSTREAM-LOCATOR`;
`E-UPSTREAM-RECORD-MISSING`; `E-UPSTREAM-STEP-UNKNOWN`; `-STEP-SCOPED`; `-STEP-INCOMPLETE`;
`E-UPSTREAM-NAME` (`ArtifactError`); `E-UPSTREAM-ARTIFACT-MISSING` (`ArtifactError`). A directory
passed as `name` (`"."`) is `E-UPSTREAM-NAME`, not a `_read` crash.

**Attack 3 — the containment rule does not overshoot.** Widening `_contained` to `if "/" in name or
…` fails **two** tests: Fixture N's positive control (`programs/a.json` and
`programs/gpt-4.1__seed29.json`) and Fixture R. Reverted, re-confirmed byte-identical, re-run green.
The three refusals: `..` and the escaping symlink each discriminate alone (mutations above); the
absolute arm does not (Minor 1).

**Attack 4 — Decision 2, by introspection.** `sorted(n for n in dir(io) if not n.startswith("_"))`
plus a parse of `class StepIO` at `76308b1` versus `db41b5a`: **added public methods `['reuse_from']`,
removed none; public `self.<field> =` assignments identical before and after
(`input_dir`, `resumed`, `run_dir`, `step_dir`)**. Live instance `vars(io)` shows the same four. The
resolver is reachable only as `self._upstream`. `reference.md:1143` already carries the
`io.reuse_from(run_id, step, name)` row, so Decision 2's *"the one method § Steps and artifacts
already documents"* is true. `ResolverIO` exposes `['input_dir', 'read_input', 'read_paths']` —
Decision 9's *"a resolver's `io` does not get it"* holds.

**Attack 5 — the placement is right beyond the mutation.** *Read and confirmed by grep:* in
`command_run`, `repo_root` is bound once at `cli.py:1965` and `output_dir` once at `cli.py:1988`, and
neither is reassigned anywhere in the function — so construction at 2329-2331 versus beside
`execute_plan` cannot change the values captured. `UpstreamResolver.__init__` assigns four attributes
and touches no filesystem, so it cannot raise, and it sits outside `RunLock` before `run_dir` exists,
which is fine for the same reason. The move is therefore **not** a proxy for a passing test: Decision
2's own written ground — *"`__init__` does no I/O and cannot raise … `allocate_run_dir` creates the
directory later, so nothing about building one may depend on `output_dir` already existing"* — is a
**live** constraint at the new site and a vacuous one at the old. The report is right that neither the
design nor the plan states the ordering, and right to have moved it; the ledger should carry it,
because a later tidy-up that moves construction down would silently re-blind the mutation.

**Attack 6 — the cache concern is reachable, and it is two findings, not an unpinned property.** See
Major 1 and Minor 3. Both are worth pinning, and both pins are cheap: a monkeypatched read counter, and
the cold/warm pair over an upstream outside `output_dir`. Ranked Major and Minor 3 respectively, for
the reasons stated in each.

**Attack 7 — the guard pin.** `git diff 76308b1 db41b5a --name-only` does not list
`tests/test_cli.py`, so arms A, B and C are untouched by this batch — **arm B was not edited**, as
required (task 7's alone). `tests/test_artifacts.py`'s diff is two hunks: the import block and a
225-line append after line 1637, so **arm D at line 952 is untouched** too. All four green: arms A/B/C
`3 passed`, arm D `1 passed`.

**Attack 8 — prose.** `artifacts.py:934-940` carries the disclaimer verbatim — *"**This is not a
boundary, and must never be written up as one.** A step can `open()` any file on the machine
regardless"* — and no test name, docstring or report sentence frames it as a sandbox or a boundary
(swept the whole diff for `sandbox`, `boundary`, `escape` in a claim position). Sweeps over the batch
diff **and** over `task-b3-report.md` and the `spec-defects.md` edit, each naming its files rather
than filtering output: **no** § Errors row claim (the single `§ Errors` mention is the true general
rule *"one row per code"*, in a test docstring, not a claim that a row exists); **no** citation of a
git-ignored path (`git check-ignore` confirms `task-*-brief.md` and `*.diff` are ignored; the report
says "the brief" and names no file); **no** count phrase — nothing matching
`six of nine|three of nine|executable|core-side blocker` appears in anything this batch wrote, so no
sentence claims a config count moved; **no** positional locator; **no** bare `x` for multiplication;
no trailing whitespace, tabs or invisible unicode. The one near-miss is the filing's *"the second half
of the same finding" below*, which quotes the target's own heading, so it survives an insertion.

**Ruling on Minor 6 (non-mapping `execution` entry).** Read and agreed: `lineage.py:226-236` records
the ruling and its grounds, and the deferred pointer was **deleted** rather than amended, which is the
right direction (*prefer deleting a claim to rewriting it*). The containment claim in that comment is
true — my end-to-end run shows an uncoded step failure is recorded `failed` with the plan continuing.

**Task 12's boundary.** `_contained` has exactly one caller (`reuse_from`); `read_upstream` and
`read_condition` are untouched, and the `_resolve` at line 697 still holds its own copy of the
predicate — correct for this batch, and task 12's to unify.

---

## Not checked, or checked only by reading

- **I did not re-run the batch's mutation 3** (reverting the containment fix to watch the new symlink
  test fail). I established the same property from the other end instead — the four-arm table above,
  built independently — so the containment behaviour is verified by running while *"this specific test
  is the thing that would catch its loss"* is taken from the report.
- **`resolves_inside_repo` is given an unresolved `repo_root` by every new test** (`tmp_path /
  "downstream_repo"`). Harmless on this machine and in production (`find_repo_root` resolves, and
  `pytest`'s `tmp_path` is already canonical), but I hit it in my own probe: with an unresolved
  `repo_root` under `/tmp` and a resolved candidate under `/private/tmp`, the predicate answers
  **False** and the containment check silently does not fire. Not a finding against this batch —
  `resolves_inside_repo` and its contract ship — noted because a future caller that does not go
  through `find_repo_root` will fail open here.
- **Whether task 6/7 closes Major 1 when it assembles `provenance.upstream`.** Out of this batch's
  charter; the guarantee is Decision 6's and the record key is task 7's, so a later slice can still
  honour it. What is wrong *today* is the docstring.
- **The `latest.txt` fallback branch** — this machine writes a real symlink, so the no-symlink path
  is unexercised, exactly as the plan's § What could not be measured says.
- **Anything requiring the `growth_screen` plugin.** Nothing in this batch claims a config executes,
  correctly.

## Tree state

Clean. `git status --porcelain` is empty apart from this review file; `src/publishable/artifacts.py`
and `src/publishable/lineage.py` were `diff -q`-confirmed byte-identical to pre-mutation copies, my
throwaway `tests/test_zz_review_b3.py` was deleted **before** the gate runs, so the 2494 / 1 / 2
reported above is the committed tree's own number with no probe file in it; `__pycache__` and
`pytest-of-*` were cleared, and the suite was run green **after** every revert and after that
deletion.
