# H9c tasks 7–10 — report

Four commits, one per task, in order.

| Task | Commit | What it is |
|---|---|---|
| 7 | `61aacb8` | The config write-back (Decision 11) |
| 8 | `7a86d1b` | Step 6 narrowed: `.env` and `required_env` (Decision 12) |
| 9 | `09f37ec` | **The behaviour change**: `run` compares against `apparatus.expected.json` (Ruling BB) |
| 10 | `7a9268d` | `reproduce` writes the expectation, once (Ruling BB) |

**Suite, read from each run's own summary line, full and unfiltered:**

| At | Passed | Skipped | xfailed | Added |
|---|---:|---:|---:|---:|
| baseline `142d3e1` | 3183 | 1 | 2 | — |
| task 7 `61aacb8` | 3191 | 1 | 2 | +8 |
| task 8 `7a86d1b` | 3204 | 1 | 2 | +13 |
| task 9 `09f37ec` | 3212 | 1 | 2 | +8 |
| task 10 `7a9268d` | 3217 | 1 | 2 | +5 |

`uv run ruff check .`, `uv run ruff format --check .` and `uv run mypy` clean at every commit.
Every mutation below was run against the **full, unfiltered** suite and every count is read from
that run's own summary line. Reverts were done by restoring a pre-mutation copy kept **outside**
the repo, verified twice — by `git diff --stat` coming back empty against the commit, and by
**re-running** the tests each mutation had failed. `git checkout -- <file>` was never used.

---

## 1. Task 7 did NOT break arm E — verified, not reasoned about

Concern 7 of batch 1's report names this task: *"task 7's write-back is the one that could break
it, and its editor is NONE."*

**Arm E is untouched and green.** Both parametrizations
(`test_h9c_arm_e_reproduce_writes_nothing_outside_its_destination[record]` and
`[bundle_member]`) pass at every commit above.

**And the arm's stated future was verified rather than argued.** A throwaway probe (written, run,
deleted — not a pin) drove `classify_operand → prepare_checkout → verify_code_hash →
restore_environment → write_config` against arm E's own fixture, from the same scratch cwd outside
all three snapshotted trees, for **both** operands. Measured, both times:

- `code_hash: matches the record over 6 files`, `restore_environment` refusing
  `E-REPRODUCE-UNLOCKED` with the checkout kept, and `write_config` returning `None` with the
  config written into the destination;
- the three tree maps — the run directory, the operand's own tree, the source repository —
  **ADDED / REMOVED / CHANGED all empty**, byte-identical before and after.

The write-back is sited on `dest`, never on `operand.path`, which is the specific hazard concern 7
names. That is the reasoning; the snapshot is the evidence, and only the snapshot is reported as
established.

---

## 2. The `null → value` case, measured and passing

Correction 27's trap, measured **before** anything was written, on a `Observations` seeded with
`{"00": {"model": "A", "region": None}, "01": {"model": "B"}}`:

| Incoming | `changed` ALONE | `record` then `changed` |
|---|---|---|
| moved value | `('model', 'A', 'Z')` | `('model', 'A', 'Z')` |
| **`null → value`** | **`AssertionError`** | **`None` (passes)** |
| `value → null` | `None` | `None` |
| identical | `None` | `None` |
| extra incoming fact | `AssertionError` | `None` (passes) |
| unknown condition | `AssertionError` | `None` (passes) |
| another condition's fact | `None` | `None` |
| condition `01` given `00`'s value | `('model', 'B', 'A')` | `('model', 'B', 'A')` |
| constant `nan` | — | `None` (reflexivity-safe) |

So the shipped code is used with `record(incoming)` **then** `changed(incoming)`, which is what
`Observer._observe_one` already does for the run's own object. **`null → value` passes**, end to
end, pinned by `test_h9c_fixture_p_arm_2_null_to_value_passes` (a `region: null` expectation, a run
that answers `region: "eu"`, exit `0`, no diagnostic, and the record carrying the **observed**
value). Mutation T9-7 (drop the `record` call, keep `changed`) fails it.

---

## 3. The behaviour change, measured on BOTH worktrees through the console script

A `main` worktree at `6ff19de` was created and `uv sync`ed; a real project was built **outside the
repository** (a `publishable new` scaffold, a project-local template declaring
`apparatus_probe: h9c_probe`, a **real installed probe distribution** reached through `PYTHONPATH`,
two swept conditions with different facts, committed). The **same** project, the same paths and the
same input data were then run under each worktree with
`uv run --directory <worktree> publishable run <config>`.

**Normalization list, written in advance**: `run_id`; every `*_at` timestamp; `wall_seconds`.
Nothing else — same project, same absolute paths, same `code_hash` tree.

| Case | `main` (`6ff19de`) | this branch |
|---|---|---|
| **No `configs/<name>/apparatus.expected.json`** | exit `0` | exit `0`. **93 `run.yaml` leaves compared, key sets equal, and every one of the 5 differences is in the normalization list** (1 `run_id`, 2 `started_at`, 2 `wall_seconds`). Run-directory trees identical. **Nothing moves.** |
| File present, facts agree | exit `0` (file ignored; record identical to a no-file run over all 93 leaves) | exit `0` |
| File present, a value **moved**, at run start | exit `0` — ignored entirely | **exit `1`**, `E-APPARATUS-UNEXPECTED`, run directory kept holding `apparatus/`, `config.yaml`, `environment/`, `identity.json`, `manifest/`, `sweep.yaml` and **no `run.yaml`** |
| File present, a fact contradicts it **mid-plan** | exit `0` | **exit `4`**, `run.yaml` written with `status: failed`, the moving observation kept in the ledger |
| File present but **malformed** | exit `0` — ignored | **exit `1`**, `E-IO-FAILED`, run directory kept with no `run.yaml` |

The real diagnostic, verbatim from the console script on this branch:

```
  error   E-APPARATUS-UNEXPECTED experiment_type
          condition `00_model=m1`'s fact `model_revision` is not the recorded one:
          `apparatus.expected.json` says r0-RECORDED and this run observed r1 — …
```

**What does not move, stated as narrowly as it is true:** a run whose config directory holds no
`apparatus.expected.json` is unchanged in every way measured above. The comparison is `None` unless
the file is there, and it is sited **after** the shipped `check_changed`, so the ordering of every
existing step is untouched. `E-APPARATUS-CHANGED` therefore wins over `E-APPARATUS-UNEXPECTED`
when both would fire — stated in the code, and it is what makes the mid-plan arm's construction
non-obvious (see § 5).

**No exit code is minted** and neither figure was chosen here: `1` and `4` both come out of
`run_status`'s shipped fold, and **both halves are armed** (arm 1 and the mid-plan arm).

**Correction 11's warning, checked:** `total_probes` does **not** inflate. Fixture Q compares a run
with the file against a control run without it, in the same test, and asserts
`provenance.apparatus.unobserved` **equal**. Mutation T9-6 (seed the run's own `Observations`)
fails it.

---

## 4. Every added or moved assertion, and the mutation that fails IT

Exactly **one shipped assertion moved**: guard-pin arm C. Everything else is an addition.

| Assertion | Mutation that fails it |
|---|---|
| **ARM C (MOVED)** `STOP_CODES == {RAISED, CHANGED, UNEXPECTED}`, `tests/test_apparatus.py` | **T9-5** remove `E-APPARATUS-UNEXPECTED` from `STOP_CODES` → it is the assertion that raises (the set-equality is first in the body and is the one the failure reported) |
| **ARM D sibling (ADDED)** `assert "E-APPARATUS-UNEXPECTED" not in APPARATUS_CODES` | **T9-4** add it to `APPARATUS_CODES` → **1 failed**, and the failing line was **read**, not inferred: `tests/test_apparatus.py:793`, which is that added line and not arm C's set-equality above it |
| `test_fixture_m_arm_1_*` (the written config hashes to the record; both paths blanked **and** marked) | T7-1 write from the byte copy |
| `test_fixture_m_arm_3_*` (a lossy round trip) | T7-2 skip the `parameters_hash` check |
| `test_the_bundle_form_writes_the_config_with_no_byte_copy_anywhere` | T7-1 (the bundle form has no byte copy at all, so the mutation cannot produce a config there) |
| `test_fixture_r_a_template_raising_at_import_is_a_redacted_diagnostic` | T8-A copy the calls without the enclosing `try` |
| `test_the_window_is_load_bearing_*` | T8-B remove the `sys.path` insert |
| `test_the_sys_path_entry_is_removed_on_the_failure_path_too` | T8-C restore on the success path only |
| `test_the_root_package_purge_is_load_bearing_across_two_checkouts` | T8-D remove the purge |
| `test_h9c_fixture_p_arm_1_*` (asserts the **identifier**) | T9-3 reuse `E-APPARATUS-CHANGED` |
| `test_h9c_fixture_p_arm_2_*`, `arm_3_*` | T9-1 compare with `!=` |
| `test_h9c_fixture_p_arm_4_*` (two conditions, different facts) | T9-2 flatten the comparison |
| `test_h9c_a_mid_plan_unexpected_fact_is_exit_four_with_a_record` | T9-5 (the loop no longer breaks) and T9-3 |
| `test_h9c_fixture_q_*` (`unobserved` equal to the control's) | T9-6 seed the run's own `Observations` |
| `test_fixture_o_arm_1_*` (mapping for mapping) | T10-2 flatten the per-condition write |
| `test_fixture_o_arm_2_*` (the file's bytes unchanged) | T10-1 overwrite an existing file |

### The mutation runs, each full-suite, each count read from that run

| # | Mutation (production code) | At | Result | Failing arms |
|---|---|---|---|---|
| T7-1 | write the config from the byte copy | `61aacb8` | **3 failed, 3188 passed** | Fixture M arm 1, arm 3, the bundle arm |
| T7-2 | skip the `parameters_hash` check | `61aacb8` | **1 failed, 3190 passed** | Fixture M arm 3 |
| T8-A | the calls without the enclosing `try` | `7a86d1b` | **2 failed, 3202 passed** | Fixture R, the failure-path arm |
| T8-B | no `sys.path` window | `7a86d1b` | **2 failed, 3202 passed** | the window arm, the purge arm |
| T8-C | restore on success only, not in `finally` | `7a86d1b` | **1 failed, 3203 passed** | the failure-path arm |
| T8-D | no root-package purge | `7a86d1b` | **2 failed, 3202 passed** | the purge arm, and the window arm |
| T9-1 | compare with `!=` | `09f37ec` | **4 failed, 3208 passed** | P arms 2, 3, 4 and the mid-plan arm |
| T9-2 | compare against the whole `facts` | `09f37ec` | **6 failed, 3206 passed** | P arms 2, 3, 4, the dirty-tree arm, the mid-plan arm, Fixture Q |
| T9-3 | reuse `E-APPARATUS-CHANGED` | `09f37ec` | **2 failed, 3210 passed** | P arm 1, the mid-plan arm |
| T9-4 | add it to `APPARATUS_CODES` | `09f37ec` | **1 failed, 3211 passed** | the ADDED arm-D sibling |
| T9-5 | remove it from `STOP_CODES` | `09f37ec` | **2 failed, 3210 passed** | arm C, the mid-plan arm |
| T9-6 | seed the run's own `Observations` | `09f37ec` | **3 failed, 3209 passed** | P arm 1, the mid-plan arm, **Fixture Q** |
| T9-7 | drop `record`, keep `changed` (correction 27's sibling) | `09f37ec` | **2 failed, 3210 passed** | P arm 2, P arm 4 |
| T10-1 | overwrite an existing expectation | `7a9268d` | **1 failed, 3216 passed** | Fixture O arm 2 |
| T10-2 | flatten the per-condition mapping | `7a9268d` | **2 failed, 3215 passed** | Fixture O arm 1, the bundle arm |

**T8-D's second failing arm is attributed rather than counted:** the window arm also depends on the
purge, because a `cohort_pilot.h9c_marker` cached by an earlier test in the same process is served
to it. The **discriminating** arm for the purge alone is the two-checkout one.

---

## 5. Where the brief, the design and the plan disagree with the code

**Do not read this as a count.** Six findings, each attributed.

**(a) The prescribed `pop(0)` mutation is BLIND, and its replacement was stated before it was
built.** `templates/discovery.py`'s `_import_file` snapshots `sys.path` and restores it **wholesale**
(`sys.path[:] = before_path`) around every `templates/*.py` it executes. Measured with a throwaway
probe printing `sys.path[:3]` at three points: the template's own
`sys.path.insert(0, "/h9c/vendored")` is visible **during** `exec_module` and **gone** afterwards,
so when `prepare_env`'s `finally` runs, `sys.path[0]` **is** its own entry and `pop(0)` removes
exactly what `remove(src_entry)` removes — *a mutation whose two branches cannot differ*. The
identity form is kept anyway (that snapshot is another module's promise, not this function's, and
it costs nothing) and the docstring says so instead of claiming a guarantee. **Three arms replace
it**, each with its own mutation above: the window is load-bearing, the restoration is total on
both paths, and the purge is load-bearing. `test_a_templates_own_sys_path_insert_does_not_survive_discovery`
carries the measurement.

**(b) Fixture P arm 1 does NOT catch *remove it from `STOP_CODES`*, contrary to design § 10.** The
design says *"the run would finish `completed`"*. Measured: at the **run-start** round the raise is
caught by `command_run`'s containment (`APPARATUS_CODES ∪ STOP_CODES`) either way — without
membership it escapes to `main`, which still prints the code and still returns exit `1`, so arm 1
stays green. The claim is true **mid-plan** only. That is why
`test_h9c_a_mid_plan_unexpected_fact_is_exit_four_with_a_record` was built, which the brief did not
prescribe; T9-5 fails it.

**(c) Fixture P arm 1 does NOT catch *add it to `APPARATUS_CODES`* either**, contrary to design
§ 10's *"arm D's addition plus Fixture P arm 1"*. T9-4 failed **exactly one** test — the added arm-D
sibling. The reason is `E-APPARATUS-CHANGED`'s own documented one: the loop breaks on a `STOP_CODES`
member before the filter is reached, so the addition is inert. Which is precisely why the assertion
was worth adding.

**(d) Fixture M arm 2's first build tested nothing, and its own control caught it.** The arm edits
the config after the commit so the clone's copy and the record's disagree. Edited
`metadata.institution` — and `covered_config` excludes `metadata` **wholesale**, so
`parameters_hash` did not move and the arm reported `identical`. Now edits
`limits.max_executions`, which `covered_config` does cover. Recorded in the helper's docstring.
**Consequence worth carrying:** the `identical`/`DIFFERS` line is a *parameters* comparison and is
blind to a `metadata`-only difference. That is correct by Decision 11's own words, and it is now
written down so nobody reads the line as *"the committed config is byte-identical"*.

**(e) `registry._claims`' docstring is false about its own importers.** It says *"the two
cross-module imports are the whole set"*. Grepped `_claims` across `src/`: **three** importers —
`validate.py:43`, `generators/experiment.py:10` and **`freeze.py:42`**. `reproduce.py` is **not** a
fourth: it uses the public `get_template` and `template_provenance` only, and names `_claims` in
prose. `templates/registry.py` is on this batch's must-not-touch list, so this is **filed** rather
than fixed — it is *a comment claiming a guarantee the code does not provide*, and the honest
repair is to delete the clause rather than to update the number.

**(f) The malformed-expectation arm's first draft asserted the wrong shape.** It asserted no run
directory at all; the read is sited beside the shipped `_probe_for` dispatch guard, which is
**after** the run directory exists and before `run.yaml`. Measured, and the arm now asserts the real
shape — a run directory with no `run.yaml` and no `executions.jsonl`, exactly what any other
pre-`run.yaml` failure leaves.

---

## 6. Every claim about other code or other tests, with what was grepped

Reported as hits, attributed, never as a count.

| Claim | Grep | Every hit |
|---|---|---|
| `.env.example` is tracked | `grep -rn "env.example\|\.env" src/publishable/scaffold.py` | `scaffold.py:92` writes it; `scaffold.py:10` is the generated `.gitignore`'s `.env` line — the example is **not** ignored. Claim holds |
| `reproduce.py` is not a third importer of `_claims` | `grep -rn "_claims" src/publishable/*.py src/publishable/*/*.py` | `freeze.py:42`, `generators/experiment.py:10`, `validate.py:43` are the three real imports; `reproduce.py:949` and `:1026` are **prose in docstrings**. See finding (e) |
| `configs/` is outside the hashed trees | `grep -rn "HASHED_TREES = "` | `hashes.py:9: HASHED_TREES = ("src", "templates")`. One hit. Claim holds |
| nothing restores `sys.modules` between tests | `grep -n "sys.modules" tests/conftest.py` | **no hits**. `registries` restores the four registry dicts; `installed` restores `sys.path` via `monkeypatch.syspath_prepend`. Neither touches `sys.modules` |
| a unique probe module name per test is the shipped convention | `grep -rn "_probe_mod.py\"" tests/test_cli.py` | `p9_`, `s9_`, `k9_`, `k9c_`, `k2_`, `t10a_`, `t10b_`, `t15_`, `loadfail_`, `decomismatch_` — ten distinct names. Convention confirmed; this batch uses one name plus an explicit `sys.modules.pop`, with the reason measured in the helper |
| batch 1's report cites the arm-C test **by name** | `grep -rn "test_stop_codes_holds_exactly_the_two_codes" .superpowers docs tests src` | `task-b1-report.md` ×2, `tests/test_apparatus.py` (the definition), `tests/test_cli.py` (arm C's citation in the guard-pin comment block), plus four H7d Part B records. **The name is left alone** and the staleness disclosed in a comment beside the assertion — a rename would break every citation above |
| `main`'s `except PublishableError` applies no redaction (correction 21) | `grep -n "except PublishableError" -A 6 src/publishable/cli.py` | one hit, `cli.py:5807-5809`: `print(f"  error   {exc.code:<20} {exc}", file=sys.stderr)`, no `Collector` in scope. Claim holds |
| the three new codes have no § Errors row yet | `grep -c` for each across the four documents | `E-APPARATUS-UNEXPECTED`, `E-REPRODUCE-CONFIG-WRITEBACK`, `E-REPRODUCE-EXPECTED-EXISTS`: **0** in all four. `apparatus.expected.json`: 3 in `reference.md` (§ Reproducing on another device), 0 elsewhere. Handed to task 14 — see § 7 |

---

## 7. Handed over, by name

1. **§ Errors owes four things, and task 14 owns them.** Rows for `E-APPARATUS-UNEXPECTED` (beside
   the other five `E-APPARATUS-*`), `E-REPRODUCE-CONFIG-WRITEBACK` and `E-REPRODUCE-EXPECTED-EXISTS`;
   and **`E-IO-FAILED`'s row must widen to three more sites** — a record with no usable
   `config.metadata.name` or one that escapes the checkout, a record whose `apparatus.facts` is not
   a mapping, and a **malformed `apparatus.expected.json`** at `run`. That last one is a new site on
   a **shipped** command, not on `reproduce`. Commit `142d3e1` already widened that row to the clone
   and sync sites; this is the same row again.
2. **Decision 12's document narrowing is task 13's prose, and this is the measurement it rests on.**
   `templates.registry.get_template` returns `None` for an installed template (`_claims` attaches
   `cls=None`; `_merged` keeps only claims with a class), **and** the plugin is installed by
   `uv sync` into the **clone's** environment, not into `reproduce`'s. So § Reproducing on another
   device's step 6 — *"lists the `required_env` variables that need values"* — **cannot** be honoured
   for a plugin-provided template, and must say so: the list is built for core's `generic` and for a
   project-local `templates/**` in the checkout; for an installed one the transcript names the
   template and its plugin and defers to the `validate` line it already prints.
   Pinned by `test_an_installed_template_names_its_plugin_and_defers_to_validate` (which asserts
   `get_template(...) is None` and `template_provenance(...) == "installed"` directly) and by its
   control, `test_a_name_no_template_claims_is_reported_as_such_rather_than_as_a_plugin`.
3. **Correction 21's cost cannot be re-measured through `reproduce` at this commit**, because
   nothing dispatches the command yet. Task 8's containment arm asserts that no exception escapes
   `prepare_env`; the *leak* half is H9b's measurement of `main`'s handler, cited rather than
   re-made. **The dispatch task is where an end-to-end credential arm becomes buildable**, and the
   positive control that already works — `validate` over the identical project printing
   `<redacted:H9C_R_TOKEN>` — is in place beside it.
4. **`registry._claims`' docstring is false about its own importer count** — finding (e). Not fixed
   here: `templates/registry.py` is on this batch's must-not-touch list.
5. **A stray `apparatus.expected.json` beside a config whose template declares no probe is inert**,
   and deliberately so: the file is read only when a probe is declared, so `observer` is `None` and
   there is nothing to compare against. No diagnostic is emitted. Disclosed rather than built on.

---

## 8. Concerns

1. **Guard-pin arm C's test function is now named `test_stop_codes_holds_exactly_the_two_codes_…`
   and holds three.** Deliberately not renamed — batch 1's report and `tests/test_cli.py`'s guard-pin
   block both cite it by that name, and *a reader greps for exactly that name and stops looking*
   cuts both ways here. The comment beside the assertion says the name is stale. **If a later slice
   renames it, it must update all eight citations grepped in § 6.**
2. **`_fixture_a` gained two defaulted keywords** (`run_kwargs`, `committed_files`). Additive — every
   existing caller is unchanged and all 74 arms in `tests/test_reproduce.py` pass — but it is now a
   shared fixture with two more shapes, and `committed_files` exists for exactly one arm.
3. **`E-REPRODUCE-EXPECTED-EXISTS` has exactly one reachable route**, a **committed**
   `apparatus.expected.json`. A second `reproduce` into the same destination cannot reach it —
   Decision 9 refuses first. Written into `write_expectation`'s docstring so a later reader does not
   re-derive it and conclude the refusal is dead.
4. **`_uv_sync` is still stubbed in every success arm** (batch 1's concern 4, unchanged), and
   nothing in this batch proves a real `uv sync --locked` succeeds.
5. **The mid-plan `E-APPARATUS-UNEXPECTED` path is narrow by construction.** Because the comparison
   sits after `check_changed`, any fact that moves *within* the run raises `E-APPARATUS-CHANGED`
   first. Reaching the mid-plan code at all takes a `null → value` transition inside the run against
   a non-null expectation — which is what the arm builds. A later slice that reorders the two gates
   would make `E-APPARATUS-CHANGED` unreachable for that shape; the precedence and its reason are in
   `_observe_one`'s comment.
