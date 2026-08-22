# H5a batch 2 (tasks 1–2) — review

Reviewed at `7686556` on branch `h5a-artifacts-write-side`. Diff: `review-b2.diff`
(`docs/reference.md` +16, `tests/test_cli.py` +98, two records — **no deletions anywhere**, so
nothing shipped could have been edited).

**Gates, all run directly in the foreground:** `ruff check` → All checks passed; `ruff format --check`
→ **93 files**; `mypy` → **52 source files**; `pytest` → **2845 passed, 1 skipped, 2 xfailed**. Tree
clean at the end of the review; both mutations reverted by editing back and verified byte-identical
with `diff` against a pre-mutation copy **and** by re-running.

## Verdicts

- **Spec compliance: PASS**, with two Majors and four Minors to close in a fix round. Every clause of
  the unification rule was built and run; the code honours all five for the ordinary case. The code
  moved nowhere: `src/` is untouched.
- **Task quality: PASS.** Task 2's fixture is a real run, is the **only** test in the suite that
  catches its own mutation, and cannot pass vacuously. The report's *"Concerns: None found"* is
  wrong — see Minor 5.

---

## What I verified by RUNNING

**1. Every clause of the cross-row rule, built as cases and executed** (`_encode_parquet` →
`_decode_parquet`, direct, plus `StepIO.record`/`finalize` and one real `run`):

| Clause (reference.md:988–992) | Result |
|---|---|
| one type round-trips, `str`/`bool` included | holds — `str`, `bool`, `int`, `float` all round-trip |
| `int` beside `float` promotes, either order | holds for both orders — `[{v:1},{v:2.5}]` and `[{v:2.5},{v:1}]` → `float`, `float` — **except above 2^53** (Minor 2) |
| `None` skipped; all-`None` and `None`+one type round-trip | holds (`[{v:None},{v:None}]`, `None`+`int`, `None`+`str`, `None`+`int`+`float`) |
| empty row set writes empty, raises nothing | holds for the encoder (`[]` and `[{},{}]` both write, decode `[]`) — unreachable for the per-unit tables (Minor 4) |
| anything else refuses, `E-STEP-RETURN-TYPE`, naming column + both types + a unit each | holds — `bool`/`int` both orders, `bool`/`float`, `str`/`int`, `str`/`float`, `list`/`int`, `bytes`/`str`, and each NumPy-beside-Python spelling. Message carries `'v'`, both `__name__`s and the `unit` value |

The `np.bool_`-beside-`bool` case names `bool` **twice** at HEAD (run and read) — known, and design
Decision 5/8 make it structurally impossible once coercion lands, so the wording *"both of the
disagreeing types"* is consistent with the branch's end state and is not a finding.

**2. `.csv` at HEAD — Correction 8 still true.** `_encode_csv([{"v":"a"},{"v":1}])` →
`b'v\na\n1\n'`, run. `bool`/`int` → `b'v\nTrue\n1\n'`; `bytes` → `"b'x'"`; `[1,2]` → `'[1, 2]'`.
`_check_column_types` has exactly one call site (`_encode_parquet`), read and grepped. The new
sentence at reference.md:997 states this truthfully and does not flatten the second ruling's
per-format asymmetry: it scopes the unification rule to the per-unit tables and asserts nothing about
structural or `bytes` cells, so it neither pre-empts nor contradicts task 9's writer/reader row split.
Swept the four documents by name (`README.md`, `design-principles.md`, `experimental-designs.md`,
`reference.md`) for `unif|promote|across rows|type clash`: **no other sentence claims `.csv` unifies
column types.** Sweep proven able to fail against a string known present (`unifies across rows` → 1
hit; `promotes to` → `docs/reference.md`).

**3. Task 2's fixture is a real run.** `run_a_project` scaffolds via `main(["new"])`, commits, and
runs `main(["run", cfg])` — a real command, not a `StepIO` probe. `data.units.measurements`
`{by: reading, collapse: {score: mean}}` is declared, the roster carries the `reading` column, and the
generated starter step calls `io.record(..., measurement="m1"/"m2")`. Documented column set verified
**against the file the run wrote**: `["unit", "measurement", "score"]`, carrying no declared attribute,
beside the sibling `["unit", "cohort", "score"]` from the same run. **What the real run showed that
reading could not:** every prior `measurements.parquet` test builds a `StepIO` through `_measuring_io`,
which never passes `units=`, so `attribute_names` is empty in all of them and none can express the
asymmetry at all; and the run also demonstrates that a *declared* `measurements` block plus a real
roster does not smuggle the axis column in — the collapse (`0.5` = mean(0.0, 1.0), `9.5`) is computed
end to end.

**4. The absence assertion discriminates, and the fixture is not vacuous.** Applied the brief's
mutation (merge the roster's attributes into the `measurements.parquet` write, mirroring the
`units.parquet` branch) and ran the **full** suite: **1 failed, 2844 passed** — the one failure is
this fixture, on `list(measurements_rows[0].keys()) == ["unit","measurement","score"]`
(`AssertionError: Left contains one more item: 'cohort'`). So the mutation is caught, the pin is
**unique in the suite**, and the report's novelty claim is confirmed by running rather than by grep.
Non-vacuity: the fixture also asserts five parquet files per side, byte-identical rows across all five
seed repeats, both column lists in order, `len == 10`/`20`, and four per-`(unit, measurement)` values —
it would `IndexError` if nothing ran.

**5. The guard pin.** `git diff 2aa0e08..HEAD --numstat` shows `tests/test_cli.py` **+98/−0**: no arm
was edited. No arm fired, in either full-suite run. Arm D's discrimination re-verified rather than
read: mutating `docs/reference.md`'s `ci95: [-0.213, -0.125]` → `[-0.113, -0.125]` fails
`test_h5a_arm_d_..._as_raw_text[REFERENCE]` **and nothing else** (`1 failed, 2 passed`); reverted,
`diff` byte-identical, 3 passed. This batch's `reference.md` insertion contains **no** worked-example
literal, and arm D compares the whole matched-line tuple, so an insertion carrying one would have
failed it. Also confirmed by direct grep that `docs/design-principles.md` carries **no** worked-example
interval literal (`0.581|0.607|0.412|0.026|0.169|0.014|0.488|0.661` → no hits), so batch 1's fact holds
and no sentence in this batch assumes otherwise.

**6. Both consistency passes.** Mechanical pass written fresh over the four documents plus `CLAUDE.md`
and the feasibility analysis (GitHub slugger, fenced blocks skipped): duplicate anchors, link and
`#anchor` resolution, trailing whitespace, tabs, invisible unicode, table column counts, empty rows.
**Clean** — the only hits are four rows my splitter mis-counts on escaped `\|` inside cells, all
pre-existing and all false positives (`reference.md:621`, `:1726`, `:3570`, `CLAUDE.md:572`). **Proven
able to fail**: injecting a bogus `#anchor`, a trailing space, a mismatched table row and a duplicate
`### The per-unit tables` heading each produced its own report. Cross-document: the quoted § Templates
phrase (*"it has nothing to collapse across a unit's repeats"*) is verbatim at reference.md:1696 and
the anchors it cites resolve; no other document mentions `measurements.parquet` at all, so no
contradiction was created outside this section. `×`/`x`: no multiplication in the insertion. No count
phrase, positional locator or config-count claim in the added prose — except the count in Minor 1. No
`§ Errors` row was added or touched (the whole `reference.md` diff sits inside § The per-unit tables).

**7. Three of the report's own greps, at its own scope.** `grep -rn "E-STEP-RETURN-TYPE" src/` → three
raise sites (`runner.py:783`, `coercion.py:226`, `artifacts.py:118`), as claimed.
`test_a_mixed_int_and_float_column_promotes_to_float_deliberately` and
`test_a_bool_and_int_column_clash_raises_rather_than_coercing` exist in `tests/test_artifacts.py`, and
`git merge-base --is-ancestor cca47ce badec28` confirms they predate the branch. `grep -rn "\.keys()) =="
tests/` over the **whole** `tests/` tree (wider than the report's two files) shows the only
`measurements.parquet` column-list assertion is the new line 16875 — the report's narrower claim holds
and so does the broader one.

---

## Findings

### Major 1 — "That is the one way the two files' column sets differ" is an overclaim, and it is false on either reading
`docs/reference.md:999`. Verified by running: `measurements.parquet` is `["unit","measurement","score"]`
and `units.parquet` is `["unit","cohort","score"]` from the same real run. The two column sets differ
in **two** ways, not one: the declared attribute, and the `measurement` column itself — which the same
sentence names one clause earlier. And the claim additionally presupposes that both files name the key
column identically, which the sentence at reference.md:985 denies (see Major 2). Recommended fix:
delete *"That is the one way the two files' column sets differ, and"* and keep the ground, which is
sound and traced correctly. This is the disagreement the batch's charter existed to find, and it was
reported as none.

### Major 2 — reference.md:985's key-column clause is false against the code, and this batch's new sentence was built beside it without checking it
`docs/reference.md:985` — *"`units.parquet`'s columns are the unit key **under the name
`data.units.key` gives it**"*. The column is literally `unit`. Verified three ways: a real run whose
config materializes `key: patient_id` writes `["unit","cohort","score"]`; a direct `StepIO`/`finalize`
probe writes `{"unit": ...}`; and `finalize` hardcodes `columns = ["unit", *attribute_names,
*recorded]` with `merged = {"unit": key}` (`src/publishable/artifacts.py`, the `if self._rows:` branch).
Design Decision 3's own text agrees — it lists `unit` as a name that *"already names a column in a
per-unit table."* **Pre-existing**, not introduced here, and the same wording is echoed in the filing at
`docs/superpowers/spec-defects.md:747`. But task 1's brief step 2 pointed the implementer at exactly
this sentence, and Major 1's new claim only reads as consistent because the clause is false. Route: the
fix is a **deletion** of the four-word clause (house rule: prefer deleting a claim to rewriting it) in
the section task 1 already owns; the filing's echo belongs to task 12.

### Minor 1 — the disjointness paragraph's count is wrong for one of the two files, and the guard it cites is the other file's branch
`docs/reference.md:1001`. *"The three groups of columns any per-unit table can hold — the unit key, a
declared attribute, and a recorded key"* — `measurements.parquet` holds a **`measurement`** column,
which is none of the three, and the same sentence treats `measurement` as a name a recorded key may not
take precisely because it is structural. Separately, the sentence's scope is *any* per-unit table while
the enforcement it names is the `measurement=` branch only: verified by probe that the **plain** branch
writes a column named `measurement` into `units.parquet` unrefused today
(`[{'unit': 'U1', 'site': 'n', 'measurement': 'HIJACK', 'v': 1.0}]`). Design Decision 9 gives that half
to task 7, so the guard-scope half closes inside this slice; **the count is wrong independent of task
7.**

### Minor 2 — the promote clause has an unstated exception, and it is the one shape the clause says cannot cost a record
`docs/reference.md:990`. Verified by running: an `int` above 2^53 beside a `float` in one column does
**not** promote — `_encode_parquet([{"v": 2**53+1},{"v": 2.5}])` raises `pyarrow.lib.ArrowInvalid`
("Integer value … outside of the range exactly representable by a IEEE 754 double"), with **no `E-`
code**. Reachable through the documented surface: `io.record("p1", {"t_ns": 1_760_000_000_123_456_789})`
beside `io.record("p2", {"t_ns": 1.5})` then `finalize()` raises it (a nanosecond timestamp is a
realistic per-unit column). **Containment, stated plainly:** `io.finalize()` sits inside `runner.py`'s
per-execution `except Exception`, so the consequence is one execution marked `failed` with an uncoded
pyarrow message — not a traceback and not a stopped run. **Does not block.** Route: either qualify the
clause or file it (the shipped pin's own docstring says this boundary must surface as a
`ContractError`, *"not a bare pyarrow exception"*).

### Minor 3 — the premise sentence's conclusion is wider than its premise
`docs/reference.md:987`. The premise is about values *a step records* (true: `record` ends in
`coerce_scalars`). The conclusion — *"what one row's cell holds is always `bool`, `int`, `float`, `str`,
or `None`"* — covers every cell in a table whose columns include declared attributes, which are not
coerced at HEAD: verified by probe that a `Unit(attributes={"tags": [1, 2]})` publishes
`[{'unit': 'p1', 'tags': [1, 2], 'score': 1.0}]`. Symmetrically, the clause list is scoped to *"every
row that recorded it"* while `_check_column_types` runs over **every** column, attributes included: a
resolver yielding `cohort=1` and `cohort="a"` refuses at `finalize` with `E-STEP-RETURN-TYPE` and a
message saying *"recorded"*. Task 6 closes the premise half inside this slice; the clause-scope half is
prose.

### Minor 4 — one clause is unreachable under the heading it is stated for, and one direction of the promote clause has no shipped pin
`docs/reference.md:991`. *"an empty row set writes an empty table and raises nothing"* — true of the
encoder (run), but `finalize` guards both writes on `if self._rows:` / `if self._measurement_rows:`, so
neither per-unit table is ever written empty; under a rule the next paragraph explicitly scopes to the
per-unit tables, this clause describes only the encoder. And the *"in either declaration order"* half of
the promote clause is pinned in one direction only — `test_a_mixed_int_and_float...` asserts
`[{v:1},{v:1.5}]`; the reverse order I confirmed by running, and no shipped test covers it.

### Minor 5 — the report's "Concerns: None found"
`.superpowers/sdd/2026-08-21-artifacts-write-side/task-b2-report.md`, § Concerns. Major 1 lives in a
sentence the report describes clause by clause, and Major 2 in the sentence the brief told it to write
beside. The report's grep discipline was otherwise good — its scope caveats are honest and all three
greps I re-ran hold — which is why the zero hid where this repo says it hides: in prose the brief
supplied as settled.

---

## What I could not check

- **Whether the `.parquet`/`.csv` asymmetry is stated truthfully in the sections task 9 owns.** The
  writer/reader row at reference.md:1214–1220 still asserts one answer for `.csv` · `.parquet`; that is
  correction 2's known defect and task 9's edit, and this batch neither touched nor needed it.
- **Arm B2's parquet sha256 under a `pyarrow` bump** — out of this batch's reach; no arm fired.
- **Whether any real project records an integer above 2^53 beside a float** (Minor 2's frequency). Not
  measurable here; only its reachability is.
