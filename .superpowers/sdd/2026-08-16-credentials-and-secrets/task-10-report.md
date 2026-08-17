# Task 10 report: the `requires_env` union over the conditions the sweep resolves

**Status:** complete.

**Commit:** (created below) — `feat: the requires_env union over the conditions the sweep resolves`

**Test summary:** `uv run pytest` — 1982 passed, 2 xfailed (baseline 1977 + 2 xfailed, plus the 5 new
tests in this task). `uv run ruff check .` clean; `uv run ruff format --check .` clean (76 files, 0
to reformat, after running `ruff format` once on the appended block — the brief's literal test code
was not itself format-clean, per the required gate); `uv run mypy` clean (43 source files).

## What was built

- `src/publishable/validate.py`: added `_check_requires_env(doc, template, c)`, called from
  `validate_config` immediately after `_check_required_env(doc, template, c)`, exactly as the brief
  specified. Body matches the brief verbatim: builds `wanted` from `parameter_spec` entries carrying
  a truthy `requires_env`; expands the config via the already-imported `expand`, guarded the same way
  `_condition_labels` guards its own `expand(doc)` call; for each condition, overlays `condition.values`
  onto declared parameters — skipping any path in `condition.selectors`, `resolve_condition_cfg`'s own
  rule; resolves each wanted parameter's value (declared, else the `Param`'s default, else skip — that
  gap is `E-PARAM-MISSING`'s); looks up `requires_env.get(value)` guarded by `except TypeError` for an
  unhashable resolved value; records the first condition to need each variable in a `dict` (insertion
  order = condition order then declared-parameter order); reports one `E-CRED-PARAM-MISSING` per
  variable `missing_env` still finds missing, at `parameters.<path>`, naming the value and the
  condition label (or "the base parameters" when `label` is `None`).
- `tests/test_validate.py`: appended the five tests from the brief verbatim (the union template, the
  `_union_project` fixture helper, the reading-A reporting test, the honouring/clean test, the
  default-fallback test, the once-per-variable-across-two-conditions test, the no-`requires_env`
  control), then ran `ruff format` on the file since the brief's literal indentation was not
  format-clean (see below).

## Decision 6's fixture, verified to separate the three readings

Derived rather than assumed, by actually running the check under each candidate implementation
(Step 6's mutations (a) and (b) *are* readings B and C):

| Reading | What it answers on the fixture (`llm.provider` choices `azure_openai`/`openai`/`ollama`, `sweep.grid` selecting the first two, `AZURE_TEST_KEY` set, `OPENAI_TEST_KEY` and `OLLAMA_TEST_KEY` unset) |
|---|---|
| **A — union over resolved conditions** (implemented) | Reports `OPENAI_TEST_KEY` alone. Confirmed: `test_the_union_is_over_the_conditions_the_sweep_resolves` passes against the shipped code, asserting `len(found) == 1` and `"OLLAMA_TEST_KEY" not in message`. |
| **B — union over all `choices`** | Additionally reports `OLLAMA_TEST_KEY`. Confirmed empirically by mutation (a): with the loop rewritten to iterate `param.requires_env` keys instead of resolved values, `found` had 2 entries — `is 'openai' in condition 'provider=openai', which requires 'OPENAI_TEST_KEY'` **and** `is 'ollama' in condition 'provider=azure_openai', which requires 'OLLAMA_TEST_KEY'` (the mutated code attributes `ollama`'s requirement to whichever condition it iterates last, here the baseline `azure_openai` row — itself evidence the two readings disagree on *attribution*, not only on *membership*). |
| **C — requirement of the written value** | Reports nothing — `azure_openai` is what `parameters.llm.provider` is written as, and its key is set. Confirmed empirically by mutation (b): with the per-condition overlay deleted, `found` was empty. |

The three answers differ (`{OPENAI_TEST_KEY}` vs. `{OPENAI_TEST_KEY, OLLAMA_TEST_KEY}` vs. `{}`), so
the fixture does separate them, as decision 6 requires.

## Mutations run (brief's Step 6)

- **(a) Union over all `choices`.** Replaced the per-condition value-resolution body with
  `for value in param.requires_env:` (iterating keys) and its lookup. Checked against the test
  body: `test_the_union_is_over_the_conditions_the_sweep_resolves` asserts `len(found) == 1`, and it
  failed with `assert 2 == 1` — `found` held both the `openai`/`OPENAI_TEST_KEY` finding and an
  `ollama`/`OLLAMA_TEST_KEY` finding attributed to `condition 'provider=azure_openai'`. This is
  exactly the mutation decision 6 sizes the fixture for; `reference.md`'s own two-choice example
  would have been blind to it. Reverted by editing back; `__pycache__` cleared; re-ran — 1 passed.
- **(b) Only the written value.** Deleted the per-condition `condition.values` overlay so `resolved`
  stayed `declared` alone. Checked against the test body: the same test's `assert len(found) == 1`
  failed with `assert 0 == 1` (`found == []`) — reading C reports nothing, since `azure_openai`'s key
  is set. Reverted by editing back; `__pycache__` cleared; re-ran — 1 passed.
- **(c) Drop the default fallback.** Changed `elif param.default is not MISSING: value = param.default`
  to fall straight to `else: continue`. Checked against the test body:
  `test_an_undeclared_parameter_falls_back_to_the_template_s_default` failed exactly as predicted,
  `KeyError: 'E-CRED-PARAM-MISSING'` from `messages_by_code(path)["E-CRED-PARAM-MISSING"]`. Reverted
  by editing back; `__pycache__` cleared; re-ran — 1 passed.

Each revert was verified by diffing the live file against a copy of the file saved immediately after
Step 3's implementation (`diff` exit 0, byte-identical), not by `git status`, and by re-running the
targeted test — never `git checkout --`.

## Step 7: the `condition.selectors` skip

Attempted the prescribed fixture — a `sweep.groups` axis named exactly `llm.provider`,
`{"sweep": {"groups": [{"by": "llm.provider", "levels": ["ollama"]}]}}` (the brief's own dict-shaped
`{"llm.provider": ["ollama"]}` does not match `sweep.groups`'s actual list-of-blocks shape; using it
verbatim produces `E-CONFIG-SHAPE`/`E-CONFIG-TYPE` for an unrelated reason — a dict where a list is
expected — before the intended path is even reached, so I corrected the shape to `sweep.groups`'s
real schema, `[{by, levels}]`, per `reference.md` § The one config file, to give the intended path a
fair chance).

**`validate` refuses the config for an unrelated reason.** Even with the group-axis shape corrected
(and after also supplying `allocation: between` plus an `assign` block to clear the allocation-arms
refusals it triggers first), the refusal that never clears is `E-SWEEP-PATH-DUPLICATE`: naming a
group axis with the same dotted path as a declared parameter (`llm.provider`) is refused outright,
independent of anything `_check_requires_env` does. Per the brief's instruction, I accept the
`condition.selectors` skip as **unpinned** by any fixture in this task, on the grounds given —
it mirrors `resolve_condition_cfg`'s own documented rule (a group cell names no parameter at all)
rather than inventing a new one — and record `E-SWEEP-PATH-DUPLICATE` as the refusal code, so the
question is not left undetermined. This fixture, corrected to a non-colliding axis name, is a
candidate for whichever slice (task 11, per the brief) owns `groups` mode.

Also unpinned, as the brief anticipates: the `except TypeError` guard around `param.requires_env.get(value)`. No fixture in this task declares a `list`-typed parameter carrying `requires_env`, and
`Param.__init__` does not forbid that combination.

## Where the brief/spec disagreed with the code

- The brief's Step 7 fixture, `{"sweep": {"groups": {"llm.provider": ["ollama"]}}}`, is shaped as a
  dict keyed by path; `sweep.groups`'s actual schema (per `docs/reference.md` § The one config file
  and confirmed by running it) is a **list** of `{by, levels}` blocks. Run verbatim, it fails at
  `E-CONFIG-SHAPE`/`E-CONFIG-TYPE` before reaching any group-axis-specific check at all, which is a
  different, uninteresting refusal from the one Step 7 is investigating. I corrected the shape to
  `[{"by": "llm.provider", "levels": ["ollama"]}]` before treating the probe as informative; the
  reshaped fixture reaches `E-SWEEP-PATH-DUPLICATE` (and, before it's cleared, allocation-arms
  refusals), which is the "unrelated reason" this report records.
- Every other detail of the brief — interfaces, fixture, docstring, message text, mutation
  predictions — matched the code and the running suite exactly; no other disagreement found.

## Concerns

None outstanding. All four gate commands are clean; the new tests exercise the union-over-resolved-
conditions path, its honouring, the default-fallback path, the once-per-variable-across-conditions
attribution, and the no-`requires_env`/`generic` control. The secret value itself was probed by hand
(outside the fixture suite): setting an env var to a distinctive string and triggering a finding
confirms the finding's message never contains that string — only the variable's *name*, the
parameter's *resolved value*, and the condition label appear, matching `reference.md`'s
`E-CRED-PARAM-MISSING` row.
