# Whole-project review — 2026-08-26, against commit `bd42f6a`

**Measured on 2026-08-26 against `bd42f6a`** (`main`, clean tree, suite **3417 passed, 1 skipped, 2
xfailed**; `ruff check`, `ruff format --check` and `mypy` clean). The charter is complete: every hardening
slice H1–H9 and every sub-slice has merged, and every row of `reference.md` § CLI reference reads `built`.

**This is not a slice review.** Every previous review in this record was scoped to one slice's own surface.
This one asks the questions no slice was in a position to ask: *does the whole arc work, are the invariants
true as a set, do the documents agree with the code as a whole, does the suite pin anything, and are the
things we shipped open actually true?*

## Method, and its limits

Five independent dimensions, each in its own git worktree, each told to **measure rather than read** and to
**prove every sweep can fail**. Two completed on the first attempt; three were killed mid-work by session
limits and were re-dispatched at a narrower scope. **One finding was retracted by its own author** and is
recorded below as retracted rather than quietly dropped.

**Every finding below is marked with how it was established**: `[verified]` means the controller reproduced
it independently at `bd42f6a`; `[reported]` means a reviewer measured it and the controller did not
re-derive it.

**What this review did not cover**, stated so nobody reads it as exhaustive: `demo`, `study`, `reproduce`,
`resume`, `freeze`, `diff`, `docs` and `dry-run` were not walked end to end (the arc review was narrowed to
the core path after its first attempt died); 26 of the 59 open filings were reached by mechanical sweep
only; 18 of the 46 multi-file error codes were not individually read against their rows; the mutation audit
ran five named mutations, not a full mutation run.

---

## Verdict

**The machinery is sound and the surface around it is not finished.**

Every load-bearing mechanism this review probed behaved correctly and is pinned by tests that fail when it
breaks: the hash fold (11 failures), the status fold (33), the per-cell partition (14), the t-interval
(35). The four documents describe a coherent system, the struck half of `spec-defects.md` is in good
order, and the feasibility analysis' four-row table re-derives exactly at HEAD.

**What is not finished is the first hour of a new user's experience**, and one contract that every plugin
author's first line of code touches.

---

## Critical

### C1 — the generated scaffold completes at exit 0 and publishes no metrics `[verified]`

The documented path `new → generate experiment → validate → run → report`, walked exactly as the generated
files direct, ends in `status: completed`, exit `0`, `aggregated: {}`, and a `report` printing `*(none)*`
three times — **with no diagnostic anywhere.**

The cause is three correct behaviours colliding, in `generators/experiment.py`:

```python
def run(self, cfg, io):
    units = list(io.units)
    for unit in units:
        io.record(unit.key, {"present": True})
    return {"n_units": len(units)}    # TODO: replace with your analysis
```

1. `{"present": True}` is a **bool** column, and a column non-numeric for every unit earns **no metric
   block** — H5b's rule, correct, and invisible here.
2. `n_units` is a step-returned scalar, so it is `basis: repeats` and gets **no `ci95`** by design.
3. The one `# TODO: replace with your analysis` sits on the **`return`**, not on the `io.record` line that
   is actually why there are no results.

**The machinery is sound**: changing that one line to a numeric record yields `value`, `ci95`, the four-way
`n`, `method: t_over_units` and a seed `repeat_spread`, and `report` renders every digit unaltered.

**The distance between the scaffold and a real interval is one line of user code. The distance between
that and *knowing* it is one line is this finding.** Two lines in the generator close it.

---

## Major

### M1 — `run` exits `4` with no printed reason `[reported]`

A step raising `AttributeError` on all five executions printed only `W-ENV-UNLOCKED` and
`run.yaml → <path>`. The cause lives in `run.yaml`'s `execution.error`. A shell swallows the `4`.

### M2 — `input_manifest_hash` is not content-addressed `[verified]`

`manifest.build_manifest` records `size`, `mtime` (`st_mtime_ns`) and `sha256` per file, and
`manifest_hash` digests **the whole dict** — mtime included. Meanwhile `verify_manifest`, the change
**detector**, compares `sha256` when the file was hashed and only falls back to size+mtime when it was
not. So for a hashed file, `touch` alone moves `input_manifest_hash` while the detector correctly reports
nothing changed. **The detector is content-addressed where it can be; the hash never is** — which is the
data half of the three-hash promise.

### M3 — `provenance.environment.manager` is a hardcoded literal `[verified]`

`cli.py:4897` writes `"manager": "uv"` unconditionally. The record asserts an environment fact nothing
measured.

### M4 — five codes are raised with no § Errors row, and the standing filing names the wrong five `[verified]`

Raised with no row: **`E-INPUT-CHANGED`, `E-PROJECT-EXISTS`, `E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`,
`E-IO-FAILED`** (27 references across `src/`).

`CLAUDE.md`'s standing filing names `E-INPUT-CHANGED`, `E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED`,
`E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS` — and **three of those five now have rows** (H9b documented the
two lock codes under its own Ruling X). So the filing is **stale on three of five and misses three others
entirely.** That is *a carried claim nobody re-derived*, sitting in the file that warns about it.

### M5 — five open filings state something false at HEAD `[reported]`

Of 33 open entries checked against code, **five are false at HEAD**, and **four of the five were closed by
the last two slices and left standing** — one of them by a commit whose own message announced the closure.
Named: the `credentials` region entry (false on four counts), `field_convention` (given a reader by
`docs.py:511`), `examples/generic/`'s stated ground, `_dispatch`'s branch order (the mapping it describes
is empty), and `required_env`'s heading.

### M6 — `io.record`'s scalar contract is pinned only by direct-call fixtures `[reported, structurally verified]`

Deleting `coerce_scalars(values, "io.record")` from the plain branch cost **2 failures out of 3417**, both
hand-constructing a `StepIO` and asserting on `io.rows()`. **Every end-to-end run test passed** with a
`list` accepted into a recorded column and a `numpy.float64` reaching `units.parquet` uncoerced.

This is the exact inverse of the other four mutations (11–35 failures each, spanning direct calls, golden
records and real runs). `io.record` is the surface **every plugin author's first line touches**, and it has
**two structurally identical enforcement sites** (`artifacts.py:795` and `:837`), each resting on one
fixture that never runs a step.

### M7 — `report` is a melt, not a report `[reported]`

15- and 16-column tables, `values | {}` as a column, unrounded floats, an Attrition table whose column set
**differs between two runs of the same config**, `n` and `repeat_spread` printed as inline YAML dicts, and
**no `run_id`, `code_hash` or provenance anywhere**. `per_repeat` metrics are in the record and rendered
nowhere.

### M8 — owner lines outlived the charter `[reported]`

24 of 59 open entries never say that no slice follows; five still use the *"whichever slice next…"* form
this file rejects by name; one heading still names the completed slice **H9** as owner; and 29 more explain
themselves by enumerating slices that no longer exist as if they were pending.

---

## Minor

- **`new` and `generate experiment` print zero bytes at exit 0** `[reported]` — no created path, no next
  step, no confirmation.
- **`cfg` accepts a write it silently discards** `[verified]` — nodes are rebuilt per access, so a held
  handle reads back mutated while every fresh access returns the declared value. `Unit` correctly refuses;
  `Node` does not. `CLAUDE.md` calls this surface *"immutable on purpose."*
- **`E-TEMPLATE-LOAD`'s row claims `reproduce` is "the one place"** it stands for an unnamed fault
  `[reported]` — there are four byte-identical sites (`reproduce`, `report`, `freeze`, `docs`).
- **Four `E-STUDY-*`/`E-REPORT-*` codes sit in § Errors `validate` reports while nothing reports them**
  `[reported]` — the dispatchers wrap none in a `try`.
- **`reference.md` § Randomness invites the numpy API two lines after ruling it out** `[reported]`.
- **A test helper ignores both of its count parameters** `[reported]` — `_h3c3_thin_config(n_control,
  n_treatment, floor)`; all seven call sites agree today, so nothing is wrong now, but a one-sided edit
  would silently convert the slice's only discriminating thin-cell fixture into a blind one. **The same
  shape as the `code`-ignoring helper this project already shipped.**

---

## Retracted

**`resume` executing with `output_dir` inside the git repository.** Filed as Critical by the invariants
review, then **withdrawn by its own author on re-examination** — *"My Critical was wrong about the
mechanism"* — before it could produce a reproduction. `command_resume` does call `_prepare_run`, which runs
`validate_config`, which owns `E-DATA-IN-REPO`. **Recorded as unproven, not as a finding.**

What survives is the architectural observation, which stands on its own: **invariant 3 is the only rule
enforced per-surface rather than at one choke point**, so its coverage is a function of each command's
argument shape rather than of the rule. A test iterating `OPERATION_COMMANDS` and asserting the refusal per
command would make a new command covered by construction.

---

## What is strong, measured rather than assumed

- **Twenty-one invariants held**, each tested by doing the forbidden thing: 40 flag invocations across
  eight operation commands, eight runs mutating one hash input at a time, every rejected repeat kind by
  name with its route, every DataFrame-shaped call on `aggregate`'s table refused, `cfg` refusing `.get`,
  `.keys`, `[...]` and `dict()`.
- **Four of five mutations to load-bearing code failed 11–35 tests each**, spanning direct calls, golden
  records and real end-to-end runs.
- **Rows with no code: zero.** Nothing documented is unreachable.
- **The struck half of `spec-defects.md` is in good order** — thirteen sampled closures, weighted to the
  oldest, all cite a specific reader and all thirteen readers exist. **Zero false closures.**
- **The feasibility analysis re-derives exactly at HEAD** — all four rows confirmed with can-fail controls,
  and all 27 cited commit SHAs exist and are ancestors of HEAD.
- **`validate` is the strongest command on the path.** `E-UNITS-KEY-MISSING` lists the columns it actually
  found; `E-NAME-DIR`, `E-DATA-UNREADABLE` and `E-UNITS-SOURCE-MISSING` all name the thing they want.

---

## The shape of what is left

Every Critical and Major here is in **the surface, the records or the pins — not in the mechanism.** No
mutation found a wrong number; no invariant probe found a broken rule; no reviewer found a run that
published something false. What they found is a scaffold that does not demonstrate the thing it exists to
demonstrate, a report that cannot be pasted into a paper, a handful of codes and filings that outlived the
slices that owned them, and one contract pinned in the wrong place.

**That is the expected shape for a project whose charter was written slice by slice.** Each slice verified
its own surface exhaustively and none owned the seam between them — which is precisely what the four
whole-branch gates kept catching within slices, and what nothing was positioned to catch across them.
