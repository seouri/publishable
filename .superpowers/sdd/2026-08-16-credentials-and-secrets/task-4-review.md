# Task 4 review: `Param.comment()` renders the requirement against every choice

Reviewed `cd78b37..5127fc9` (`review-cd78b37..5127fc9.diff`), against `task-4-brief.md`,
`task-4-report.md`, `CLAUDE.md`, `docs/reference.md` and the current tree.

Per the controller's instruction, the "prompt injection" thread in the report and ledger is out of
scope: it was the controller's own uncommitted ledger write, already corrected in `progress.md`.
The implementer's refusal was correct and is not reviewed here.

## Verdicts

1. **Spec compliance — ✅** (the string the brief's *Produces* clause names is delivered exactly)
2. **Task quality — ❌** (one Important finding: the report's site-by-site disposition asserts
   "none is falsified" and "Disagreements: None", and one of the four `reference.md` sites it
   dispositioned **is** falsified — by the layout, which a string-level check cannot see)

## What I verified, and how

**The invariant (`parameter_spec` is the single source of truth).** ✅ Verified by construction, not
by reading. `Param.__init__` (`src/publishable/param.py:56-74`) accepts `requires_env` only with
`choices`, and only when the mapping is **total** over them; `_choice_label` renders exactly that
shape — one label per declared choice, the choice's variables comma-joined, bare when the list is
empty. I exercised the boundary directly:

| Constructed | Rendered |
|---|---|
| `requires_env` without `choices` | `ValueError: requires_env requires choices: …` — unconstructible, so no comment shape exists for it |
| `choices=["a","b"], requires_env={"a":["K"],"b":[]}` | `choices: a (needs K) \| b` |
| `requires_env={"a":[],"b":[]}` | `choices: a \| b` |
| `int` choices, `requires_env={1:["K"],2:[]}` | `choices: 1 (needs K) \| 2` |

No comment describes a shape the constructor rejects, and no accepted shape renders unannotated.

**`requires_env` did not become a constraint.** ✅ The "one constraint claims it, else `help`" rule
is intact, and holds more strongly than the review brief assumed: a `Param` carrying `requires_env`
and **no other constraint is unconstructible**, because `requires_env` requires `choices` and
`choices` is itself the first constraint in `comment()`'s precedence chain. So `requires_env` can
never claim the comment on its own and can never displace `help` — confirmed `Param(str,
default="a", help="H").comment() == "H"` is untouched, and that `requires_env` + `pattern` + `help`
still renders `choices: a (needs K) \| b`, i.e. the pre-existing precedence, unchanged. The amended
docstring's three claims — "not a constraint", "see this module's docstring", "against *every* choice
rather than the written one" — are each true of the code, and the module docstring it defers to
(`param.py:5-9`) does state the boundary.

**Exact strings.** ✅ Both new tests assert whole rendered strings with `==`
(`tests/test_param.py:188-191`, `:201`). No substring assertion was introduced.

**The regression sites — byte-identity measured, not carried.** ✅ for the identity claim. I did not
accept the report's count. I materialized `generic`'s config with the current `comment()`, then
monkeypatched the pre-task-4 `choices` branch (`" | ".join(str(c) …)`) back in and materialized
again: **the two outputs are byte-identical (2583 bytes)**, and `generic`'s `parameter_spec` declares
no `requires_env` at all, so the identity is structural rather than coincidental. Spot-checked four
of the six sites: `tests/test_materialize.py:139` (present verbatim in the fresh render),
`docs/reference.md:1588` (the § Templates constraint-table row, which correctly still omits
`requires_env` — design-spec item 5 owns it, confirmed at
`2026-08-16-credentials-and-secrets-design.md:91`), `docs/reference.md:3451` (`instrument.vendor`,
no `requires_env`), and `docs/reference.md:1637` — which is Important 1 below.

**The mutations.** ✅ Re-ran mutation (b) myself (`if not needs:` → `if needs is None:`), reverting by
editing the file back from a scratchpad copy — never `git checkout --` — with `__pycache__` cleared
and green re-confirmed after each. It reddens
`test_a_choices_comment_carries_each_value_s_credential_against_every_choice` on exactly the
`ollama (needs )` suffix. Checked against the test bodies: both new tests are exact equalities over
fixtures whose annotations differ per choice, so both prescribed mutations discriminate for the
stated reason and not by accident.

**Full gate re-run at HEAD, after every mutation was reverted** (`git diff` empty over `src`,
`tests`, `docs`): `uv run pytest -q` → **1964 passed, 2 xfailed**; `ruff check` clean;
`ruff format --check` → 74 already formatted; `mypy` → no issues in 42 source files.

**(a) A check that could not fail** — every test added has a single-line mutation that reddens it,
each verified empirically:

| Test | Mutation that fails it |
|---|---|
| `…carries_each_value_s_credential_against_every_choice` | `if not needs:` → `if needs is None:` (verified: fails on `ollama (needs )`); also `_choice_label(self.default)` in the join |
| `…names_both_in_its_own_parenthesis` | `', '.join(needs)` → `' '.join(needs)` — **verified: fails this test and only this test** (1 failed, 17 passed), so it is not merely riding on the first test's fixture |

**(b) A comment or docstring claiming a guarantee the code does not provide** — read every prose line
in the diff. The amended `comment()` docstring is accurate, clause by clause. `_choice_label` carries
no comment. The report's *code* descriptions match the code; its *disposition* claims do not (below).

## Findings

**Important 1 — `docs/reference.md:1635-1638` shows a config layout `init` does not produce, and the
report dispositioned that exact site as "not falsified".** The section's own sentence is
"**`init` renders the requirement into the `choices` comment**", followed by a yaml block that puts
the comment **on its own line** beneath the value. `materialize.py:86-89` never does that: it always
appends the comment to the value's line, padded to column 36 (`pad = " " * max(1, 36 - len(entry))`).
Verified by rendering a throwaway in-process template declaring exactly the section's `Param`:

```
'  llm:'
'    provider: azure_openai          # choices: azure_openai (needs AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama'
```

against what the document shows:

```
  llm:
    provider: azure_openai
    # choices: azure_openai (needs AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama
```

The report's "modulo the `# ` prefix `materialize` prepends" is what hid it — what `materialize`
adds is not a prefix but a *position*, and a string-level check cannot see position. This is the
slice's recurring shape (prose written ahead of the code, then confirmed against the part of the code
that agrees with it), and it is the reason for the ❌: the report states "Disagreements between
brief/spec and code: **None**" while this one was live and inside the four sites it enumerated. The
code is right and the document changes, per `CLAUDE.md` — one line, replacing the two-line block with
the trailing form quoted above. Spec compliance stays ✅ because the brief's *Produces* clause names
only the string, which is delivered character-exact.

**Minor 2 — the mutation set does not reach choice *ordering*, and a suite-green mutation exists.**
Nothing pins that the comment lists choices in `choices` order rather than in `requires_env` key
order. Verified: replacing the join's iterable with `(self.requires_env or self.choices)` leaves the
**entire suite green — 1964 passed, 2 xfailed**. Both new fixtures declare `requires_env` keys in the
same order as `choices`, which is `CLAUDE.md`'s "a fixture with too few elements to distinguish the
candidate orderings" applied to key order. **Advisory, not blocking**: no passage in `reference.md`
specifies choice ordering, so this is a missing pin rather than an unpinned spec claim, and today's
behaviour (choices order, matching `check()`'s error message) is the right one. Closing it costs one
line — declare one fixture's `requires_env` keys reversed relative to its `choices`. Probe reverted.

**Minor 3 — "pins `[]` as 'needs nothing' rather than as a missing key" overstates what mutation (b)
can pin.** The brief says it and the report repeats it. Because `__init__` enforces totality over
`choices`, a *missing key* is unconstructible, so no fixture can distinguish `[]` from a missing key
— and `_choice_label`'s `(self.requires_env or {}).get(choice) **or []**` fallback for a missing key
is unreachable defensive code. What the mutation actually pins is narrower and still worth having:
an **empty list renders bare**. The report is half-aware (it notes the `is None` branch is dead) but
keeps the stronger sentence. Prose only; the dead `or []` is harmless.

**Minor 4 — mutation (b) reddens three tests, not the one the report highlights.** With
`requires_env=None`, `{}.get(c) or []` yields `[]`, which under `needs is None` takes the annotated
branch, so the no-`requires_env` control also goes red (`choices: a (needs ) | b (needs )`). The
report names only the intended test and never claims exclusivity, so nothing it says is false —
recorded because "which tests a mutation reddens" is evidence a later reader will reuse.

## Not findings, checked and cleared

- **The worked example's comment column is off by one against the render** — `reference.md:111-112`
  put `#` at column 35, `materialize.py` puts it at 36. Pre-existing, untouched by this diff, and
  outside this task; noted only because it is adjacent evidence that these examples were never
  checked against a render. Worth a separate sweep, not a fix here.
- ` M .superpowers/sdd/.gitignore` in the working tree is the known `sdd-workspace` clobber described
  in `CLAUDE.md`, present before this review began.
- Step 6's accepted gap (no end-to-end `materialize` coverage of the presence case, since no template
  in the tree declares `requires_env`) is correctly stated in both brief and report, and correctly
  deferred to task 10's fixture. Note that Important 1 is precisely the defect that gap left open —
  the throwaway template I rendered to find it is roughly the fixture Step 6 declined to invent.
