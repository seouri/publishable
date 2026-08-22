# Task 13 (+ arm E) — batch review

**Spec compliance: PASS.** The five arms are the five the brief and the second controller ruling
call for, on the surfaces they name; nothing outside `tests/` was touched, so no `§ Errors` row was
added and none was owed; arm B2's recapture condition is stated in advance in its own docstring; and
no config count is claimed anywhere in the diff.

**Task quality: PASS with findings.** Every arm discriminates — I found a failing mutation for each
of the five, by running — and arm E discriminates in both directions. Four Majors and three Minors
below; all close by editing this batch's own tests and report, none needs a source change. The one
that matters downstream is Major 1: arm E is labelled *NO AUTHORIZED EDITOR* and task 9 will
certainly break half of it.

Gates re-run at HEAD (`9fdb565`), foreground, unfiltered: `uv run pytest` → **2843 passed, 1
skipped, 2 xfailed**; `ruff check` clean; `ruff format --check` **93 files**; `mypy` **52 source
files**. Tree clean, verified by `git status --short` and by `diff` against pre-mutation copies of
all four files I mutated (`artifacts.py`, `design-principles.md`, `reference.md`, `README.md` — all
four byte-identical after revert).

---

## Findings

### Major 1 — arm E is labelled "NO AUTHORIZED EDITOR", and task 9 will break its `.csv` half

`tests/test_artifacts.py:2498` ("NO AUTHORIZED EDITOR"), assertions at `:2529` and `:2533`.

The same docstring, twelve lines lower, says *"A LATER task (task 9) IS authorized to change `.csv`'s
behaviour from 'stringifies silently' to 'raises `ContractError`'"*. That is not a hypothetical:
plan task 9 step 5 (Fixture S) builds exactly that refusal, so `csv_list == [{"v": "[1, 2]"}]` and
`csv_bytes == [{"v": "b'x'"}]` **must** fail when task 9 lands. And task 9's step 8 tells its
implementer to *"confirm arms A, B1, B2 and C are green"* — arm E is absent from that list, because
the plan predates it.

**Verified by:** reading plan task 9 steps 5 and 8, plus running the two mutations. Simulating task 9's
`.csv` half (a pre-pass decoding `bytes` in `_encode_csv`) failed arm E and nothing else; simulating a
`.parquet` narrowing failed arm E and nothing else.

So task 9's implementer meets a red test whose header says its firing *"is a finding"* and whose body
says the change is authorized — ambiguous authority on a pin, which is the quiet-weakening shape
`CLAUDE.md` names. Fix: split arm E into two tests — the `.parquet` capability half with genuinely no
editor, and the `.csv` half naming **task 9 as its sole editor with the post-edit state specified in
advance** (H8a arm B's precedent), leaving the never-changes property (`.csv` must not return an
actual `list`/`bytes`) in the no-editor half.

### Major 2 — arm A's docstring claims two discrimination classes its fixture cannot provide

`tests/test_cli.py:16726-16728`: *"it catches `int` silently promoted to `float`, a `bool` becoming an
`int`, a `str` becoming its `repr`, a **`None` becoming something else**, and any reordering."* The
fixture records `{"present": True, "score": float(i)}` against `unit`/`cohort` strings — **no `int`
column and no `None` column exist**.

**Verified by running:** with `_encode_parquet` mutated to promote `int`→`float` *and* map `None`→
`"MISSING"`, arm A stays **green**. Only arm B2 fails — the version-coupled tripwire this docstring
says arm A exists to be independent of. Both columns are reachable: a probe run recording
`{"present": True, "score": float(i), "n": i, "note": None}` produced
`{'unit': 'str', 'cohort': 'str', 'present': 'bool', 'score': 'float', 'n': 'int', 'note': 'NoneType'}`
in `units.parquet`, so the fix is two more recorded columns and a recapture, not a deletion. This is
brief-supplied prose repeated as established (the brief's own *"why this arm is the load-bearing one"*
makes the same five claims) — the shape `CLAUDE.md` says all six "zero disagreements" reports hid in.
It must close in this batch: only a capture taken before anything moves can pin it.

### Major 3 — arm D leaves eight worked-example lines in `reference.md` uncovered, including one CLAUDE.md singles out

`tests/test_cli.py:16768` (`_H5A_ARM_D_LITERALS`).

**Verified by running** a scan for the worked example's other bounds: `docs/reference.md` lines 750,
1487, 1496, 2119, 2719 (`ci95: [0.517, 0.683]` — spearman's per-condition interval, five
occurrences), 2221 (`delta: -0.169`), 2222 (`ci95: [-0.213, -0.125]` — kendall's contrast, the
interval CLAUDE.md says *"must not be narrowed back"*) and 2807 (`correction_level: 0.0071`) contain
none of the 15 literals and are therefore in none of arm D's tuples.

Two causes. The literal list writes `−0.169` / `−0.007` with a **Unicode minus** (U+2212), as
`CLAUDE.md`'s prose does, while `reference.md`'s YAML blocks write ASCII `-0.169`; and the
per-condition bounds `0.517 0.683 0.347 0.477 0.213 0.125` are not in the list at all.

**Verified by running:** I changed `ci95: [-0.213, -0.125]` to `[-0.113, -0.125]` in
`docs/reference.md` and arm D stayed **3/3 green**. The brief prescribed the 15 literals, so this is
not a deviation from the brief — but the arm is presented (report, and the plan) as what makes
§ The worked example *provably* untouched, and that overstates what it covers. Fix: add the ASCII
spellings and the six missing bounds and recapture.

### Major 4 — a report claim about other tests is false, and its cited evidence is about a different corpus

`.superpowers/sdd/2026-08-21-artifacts-write-side/task-b1-report.md`, arm A bullet: *"No existing test
reads `units.parquet` for a real run — the brief's own § Testability note (no core reader of this file,
checked via `grep -c parquet` across `report.py`/`study.py`/`diff.py`/`lineage.py`)."* The claim is
about **tests**; the evidence is about **`src/`**.

**Verified by running** `grep -rn "units.parquet" tests/`:
`tests/test_acceptance.py::test_the_interval_matches_an_independent_computation` (lines 526–553) reads
a real run's `units.parquet` with `pq.read_table` and recomputes the interval from it; `tests/
test_report.py:328` reads it through `read_condition` inside a real run; `tests/test_cli.py:8967`
iterates `sorted(run_dir.rglob("units.parquet"))`. Arm A's *novelty* survives narrowly — none of the
three pins column **order** or per-column **types** — but the sentence as written is exactly the shape
`CLAUDE.md` says six consecutive reports hid a false claim in. Fix: correct the report line to the
narrow claim, and name what was grepped in `tests/`.

### Minor 1 — arm A locates its artifact by filesystem iteration order

`tests/test_cli.py:16748`: `parquet_path = next(doc["run_dir"].rglob("units.parquet"))`.

**Verified by running** a probe of the same run shape: the run writes **five** `units.parquet` files
(`seed08/`, `seed17/`, `seed27/`, `seed76/`, `seed84/`). The pin asserts on whichever `rglob` yields
first — a position, not an identity, in the same currency as the `pop(0)` fault. All five come from
one code path so the assertion holds today, but the docstring says *"a real run's `units.parquet`"*
singular. The sibling that already got it right is in the same file: `tests/test_cli.py:8967` uses
`sorted(...)` and iterates all of them.

### Minor 2 — arm E does not pin element types inside the `.parquet` list cell

`tests/test_artifacts.py:2521-2522`. **Verified by running:** with `_encode_parquet` mutated to
promote list elements `int`→`float`, arm E stays **green** — `[1, 2] == [1.0, 2.0]` is `True` and the
container is still a `list`. That is one level deeper than the `['1', '2']` case the second ruling's
"assert type as well as value" instruction named, and it is the honest limit of the arm. Fix: assert
`[type(x) for x in pq_list[0]["v"]] == [int, int]`.

### Minor 3 — redundant positional locators

`tests/test_cli.py:16700` (*"…`test_h8c_arm_b_publishable_all_is_a_full_sorted_list` immediately
above"*) and `tests/test_artifacts.py:2446` (*"…`_clash_raises_rather_than_coercing` above"*). Each
names the test it points at, so nothing is load-bearing — but this repo has been wrong on a positional
locator twice, and the name alone carries the reference. Drop the "above".

---

## The two disclosures, adjudicated

**The prescribed mutation (ii) was blind, and the report is right about why.** **Verified by running**
the `float()`-wrap exactly as prescribed: `ValueError: could not convert string to float: 'hello'` and
`TypeError: float() argument must be … not 'list'` at `src/publishable/artifacts.py:133`, before any
table is built; arm A fails through `run_a_project`'s own `assert 4 == 0`, not through the
`type(v).__name__` row. The disclosure is accurate — and it is not the resolution: **a blind mutation
owes a replacement**, and arm A's type row therefore shipped unproven. I supplied one and ran it: in
`_encode_parquet`, `int(v) if type(v) is float and v == int(v) else v`. Arm A **failed on
`assert 'int' == 'float'` alone**, with every value assertion passing (`0 == 0.0`, `9 == 9.0`) and
**arm B2 green** (its floats are 1.5/2.5, non-integral). So the type row carries power no other
assertion in the suite carries for this file, independently of the locked `pyarrow`. A second
replacement — bool→int — failed arm A (`assert 1 is True`) and arm B2. Record the replacement; the arm
itself is sound.

**`docs/design-principles.md` carries no worked-example interval literal — confirmed, and it is a fact
about the documents.** **Verified by running** `grep -nE '0\.(581|488|661|607|412|026|059|014|169|007|517|683|347|477|213|125)' docs/design-principles.md` → **no output**. The file's entire
worked-example footprint is three hash-identity lines (121–123: `8e21`, `3d8a`, `6b1f`). So
§ The worked example's cross-document coverage is *thinner* in `design-principles.md` than
`CLAUDE.md`'s "one experiment runs through README, `design-principles.md`, and `reference.md`"
implies — the intervals live in two of the three files, not three. Substituting a hash digit for the
brief's "interval bound" was the right call, and the mutation still exercised the property (three
independent tuples): **verified by running** — mutating `sha256:8e21…` → `8e22…` failed
`[DESIGN_PRINCIPLES]` only.

---

## Arm-by-arm discrimination, all verified by running

| Arm | Mutation that fails it | What else failed | New power, or already shipped |
|---|---|---|---|
| A | `sorted(row)` in `_encode_parquet` (order); float→int for integral values (type row); bool→int (value+type) | B2 on the first and third; **nothing** on the second | New on **column order** and **per-column type**. Not new on "reads `units.parquet`" — see Major 4 |
| B1 | `lineterminator="\n"` → `"\r\n"` | nothing | New: no other test compares this file's bytes (the mutation failed B1 alone) |
| B2 | `sorted(row)`; bool→int; int→float; None→`"MISSING"` | A on the first two only | New; and the last two show B2 catching what arm A currently misses (Major 2) |
| C | dropping both type names from `_check_column_types`' message | nothing | The two **refusals** are already pinned by `test_a_bool_and_int_column_clash_raises_rather_than_coercing` / `…str_and_int…` (both exist, greped). New power is only the `io.write` route |
| D | a hash digit in `design-principles.md`; an interval bound in `README.md` and in `reference.md` | each failed **only its own** parametrization | New; incomplete — Major 3 |
| E | narrowing `.parquet` (raise on `list`/`bytes`); "fixing" `.csv` (decode `bytes` to `str`) | nothing either time — B1, B2, C stayed green | New, both directions |

**Arm C's substrings survive task 9's authorized edit — verified by running it.** I applied both
halves of task 9's message change (deleted the surface enumeration from `_check_column_types`, and
wrapped `WRITERS[suffix](obj)` in `except ContractError` re-raising with `f"{name}: {exc}"`) and ran:
all 8 h5a arms green and all **138** tests in `tests/test_artifacts.py` green. And none of `'v'`,
`bool`, `int`, `str` appears anywhere else in the message or in the artifact name task 9 prefixes
(`clash.parquet`) — so no substring is satisfied by neighbouring output.

**Arm B2's tripwire premise holds.** `uv.lock` pins `pyarrow 25.0.0` (verified). **No H5a task touches
`uv.lock`** — verified by grepping the whole plan: the only four hits are inside task 13's own
docstring text and the plan self-review. (`6b1f` in arm D's tuples is the *documented* lock hash
prefix, not the file.)

**Arm D locates by literal, not by ordinal** — the helper at `tests/test_cli.py` filters
`text.split("\n")` by `any(literal in line …)`, read and confirmed. And **no captured arm D line sits
in a `reference.md` section H5a edits**: § The per-unit tables (975–987), § Errors core raises
(1071–1143) and § Steps and artifacts (1143–1229) contain none of them; the captured lines live in
§ Run identity, § Weighted samples, § What isn't a repeat, § The unit table is the inference base,
§ Reporting strata, § Pre-registration, § study.yaml and § Reproducing on another device. One caveat
worth carrying rather than filing: plan task 12 lists `README.md` / `design-principles.md` /
`reference.md` as *"read, and edit only if the sweeps require it"*, which is a conditional editor arm
D's "no authorized editor" sentence does not mention.

## Prose and scope

Diffstat is three files — `tests/test_artifacts.py`, `tests/test_cli.py`, the report. No document was
edited, so **no `§ Errors` row was added** and none was owed. **No config-count claim** anywhere (the
only `config`/count-shaped hits in the diff are captured document literals inside arm D's tuples).
**No bare `x` used as multiplication.** All seven test names quoted in the new docstrings exist —
greped, each found. Positional locators: Minor 3.

## What I could not check

- Whether `pytest`'s `rglob` ordering could ever yield a *different* `units.parquet` first on another
  filesystem — Minor 1 is a structural objection, not an observed failure; all five files are written
  by one code path.
- Whether arm B2's hex is stable across `pyarrow` patch releases. That is what makes it a tripwire,
  and its recapture condition is correctly stated in advance.
