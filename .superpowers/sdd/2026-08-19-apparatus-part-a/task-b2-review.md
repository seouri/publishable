# H7d Part A — Batch 2 review (tasks 4–8)

**Reviewed at `6df82fe` on branch `h7d-apparatus-part-a`.** Every claim below marked *verified by
running* was produced by executing something in this working tree; everything else is marked *read*.
No tracked file was modified: `src/publishable/apparatus.py` and `tests/test_apparatus.py` were
copied to the scratchpad before the one mutation this review applied, reverted by editing back, and
confirmed byte-identical to their copies afterwards (`diff` clean). `git status --porcelain` shows
this review file alone, untracked, which is the deliverable — batch 1's `task-b1-review.md` was
tracked by the ledger commit that followed it, and this one should be added the same way
(`git add -f`, since `sdd-workspace` clobbers that `.gitignore` to a bare `*`).

## Verdicts

**Spec compliance: FAILS on one point, otherwise compliant.** `warn_unanswered` fires
`W-APPARATUS-UNANSWERED` for an **undeclared** fact that came back `null`, contradicting Decision 8's
opening clause (*"a **declared** fact that came back `null` produces `W-APPARATUS-UNANSWERED`"*),
Decision 4's fourth row, and `reference.md` § The apparatus core can only observe — *"What the
declaration adds is a warning when the fact comes back `null` … and an `unobserved` count"*. Verified
by running, and **it is a plan defect first**: task 7's brief prescribes the signature
`warn_unanswered(self, c: Collector) -> None` with no `declared` parameter, so the filtering capability
was absent from the code block the implementer was handed. Everything else this batch owns holds:
no call site was added, Decision 5's `__post_init__` prohibition is honoured, five codes not four are
minted, the credential check refuses rather than redacts and matches by exact value, the ledger's five
keys and `<nn>_<label>` condition key are as ruled, and no sentence anywhere in the batch claims a
config was unblocked.

**Task quality: adequate, with a soft spot exactly where the batch is highest-stakes.** All ten
prescribed mutations were run and two were adjudicated rather than faked — the right instinct, and the
adjudications are arithmetically correct. But **both adjudications left the falsified claim standing in
the committed docstring**, and the credential check — the thing the brief called the highest-stakes item
— has **no test in the whole suite that can distinguish exact-value matching from a pattern heuristic**,
which I verified by running the brief's own mutation against the full suite and watching it pass.

---

## Findings

### Major 1 — an undeclared fact that returns `null` produces `W-APPARATUS-UNANSWERED`

`src/publishable/apparatus.py:255` (`Observations.warn_unanswered`), reachable via `:262` — the loop
iterates `self._facts_by_condition[condition]`, which `record` (`:216`) populates from **every** key a
probe returned. `warn_unanswered` takes no `declared` argument at all.

**Verified by running:**

```
obs.record("00_baseline", {"model_revision": "r1", "undeclared_diag": None})
→ FINDING: W-APPARATUS-UNANSWERED | condition `00_baseline`'s fact `undeclared_diag`
  came back `null` on 1 of 1 probes
```

`unobserved` gets this right (declared-only, `:243`); the warning does not. **Attribution: this is a
plan defect, not the implementer's alone** — task 7's brief gives the signature as
`def warn_unanswered(self, c: Collector) -> None: ...`, with nothing to filter by, and the built code
matches the brief exactly. Batch 1's ledger entry records its Major 3 the same way, and the precedent
applies here. The design is unambiguous all the same: Decision 8's ruling opens *"a **declared** fact
that came back `null` produces `W-APPARATUS-UNANSWERED`"*, and `reference.md` § The apparatus core can
only observe makes the warning *the thing declaring a fact buys* — the sentence is
the reason the section gives for declaring a fact you may not be able to observe — so a warning that
fires without a declaration deletes the distinction. Decision 8's grain ("one finding per (condition,
fact)") and correction 3's change of *what it is computed from* neither of them licensed widening the
**set** of facts.

**No fixture separates the readings**, which is why the suite is green:
`test_unobserved_counts_declared_facts_only_and_counts_every_probe`
(`tests/test_apparatus.py:333`) is the only test with an undeclared fact and it gives that fact
**non-null** values (`"x"`, `"y"`), so the undeclared branch of the warning is never exercised. This is
the *seam named in a brief and instantiated by no fixture* row.

**Fix:** give `warn_unanswered` the declared list — which task 11's call site must then pass, the
same list it already passes to `unobserved` — and skip a pair whose fact is not in it; add the
discriminating fixture (an undeclared fact returning `null` → zero findings, asserted beside a declared
null pair that must report, so the control is not an absence-only assertion).

### Major 2 — a fact value with elementwise `__eq__` escapes `check_facts` as an uncoded `ValueError`, but only when a credential is declared

`src/publishable/apparatus.py:166` — `if value == cred_value:` is evaluated on the **raw** returned
value, before the scalar walk that would have refused it.

**Verified by running:**

```
check_facts(Apparatus(facts={"x": np.array([1,2])}), [], probe_name="p", credentials={})
  → ContractError E-APPARATUS-FACT-TYPE
check_facts(Apparatus(facts={"x": np.array([1,2])}), [], probe_name="p", credentials={"TOK":"lab7"})
  → UNCODED ValueError: The truth value of an array with more than one element is ambiguous
```

So whether core answers with a diagnostic or with a traceback depends on whether the template declared
a credential — a fail-open on the exact axis Decision 5's ground names (*"discovering that at
`json.dumps` is a traceback rather than a diagnostic"*), and the same class `E-APPARATUS-RETURN` was
minted to close. A `ValueError` is not a `PublishableError`, so it is outside `APPARATUS_CODES` and
outside `cli.main`'s `except PublishableError` — batch 3's wrapper (plan correction 10) will not catch
it either. Read, not run, for that last sentence: no call site exists yet.

No credential is disclosed by the message, which is why this is Major and not Critical.

**Fix without disturbing the ruled ordering:** guard the comparison with `isinstance(value, str)`.
Credential values are always `str`, so the guard is behaviour-preserving for the property Decision 6
states, and it keeps the credential check ahead of the scalar walk.

### Major 3 — nothing in the suite can tell the exact-value check from a pattern heuristic; the brief's own mutation is blind at full-suite level

`src/publishable/apparatus.py:163–172`; tests at `tests/test_apparatus.py:255`, `:270`, `:285`.

**Verified by running the full suite.** I applied the brief's exact heuristic in place of
`value == cred_value`:

```python
if isinstance(value, str) and (
    len(value) >= 20 or any(c.isdigit() for c in value) and value.isalnum()
):
```

→ `2392 passed, 1 skipped, 2 xfailed` — **the entire suite stays green.** Reverted by editing back;
confirmed by behaviour (a random-looking non-credential is kept again) and by `diff` against the
scratchpad copy.

The reason is that the three credential tests cover only two of the three cells: *value equals a
declared credential* (refused) and *credentials is empty* (kept). The missing cell is the one
Decision 6's ground actually turns on — *"a pattern check … fails **closed** on a config value that
happens to look random"* — a **non-empty** `credentials` mapping beside a fact value that is
credential-shaped but is **not** one of the declared values. Under the real code that value is kept;
under the heuristic it is refused. Verified by running both ways:

```
facts={"model_revision": "gpt-5.5-2026-06-11x9f3a2b8c"}, credentials={"INSTRUMENT_API_TOKEN": "lab7"}
  mutant   → refused, E-APPARATUS-FACT-CREDENTIAL
  reverted → kept
```

`test_a_value_core_never_read_is_not_matched` (`:285`) is described as *"the control that keeps the
check from being a string-similarity heuristic in disguise"*, but it passes `credentials={}`, so the
inner loop never runs at all — a control that passes identically if nothing ran.

**Adjudication of the implementer's disagreement 1:** their conclusion (the brief's formula does not
discriminate) is **correct and understated** — it does not discriminate at *suite* level either, not
merely for the named test. Their substituted length-only heuristic **does** genuinely discriminate for
the named test, verified by running (`"lab7"` is 4 characters, so the refusal test fails under it), so
the substitution was legitimate and the shipped code is exact equality as ruled. The defect is the
missing third cell, which neither mutation reaches.

**Fix:** add the third-cell test above. It is the only thing in this batch that can fail if the
credential check is ever replaced by a pattern.

### Major 4 — two committed test docstrings assert claims the implementer's own report contradicts

CLAUDE.md's *a comment or docstring claiming a guarantee the code does not provide*, and its
*a test whose name claims the guarantee* — with the aggravating detail that both were **found** during
execution, written up in the report, and left in the code. The rule is *prefer deleting a claim to
rewriting it*.

- `tests/test_apparatus.py:255–260` — *"a random-looking value makes an exact-value check and a
  heuristic AGREE, so the mutation below would have two branches that cannot differ"*, i.e. `lab7` was
  chosen so a heuristic would **not** flag it. Report disagreement 1 says the opposite: the brief's
  heuristic flags `lab7`. Verified by running (see Major 3).
- `tests/test_apparatus.py:348–352` — *"three declared facts over **six** observations, arranged as
  **Fixture N**"* and *"per-call emission would produce **eight**"*. Verified by running against the
  committed fixture: it makes **four** `record` calls carrying **four** null observations, so per-call
  emission yields **4**, not 8; and it is not Fixture N (the plan's Fixture N is a six-line `run`-level
  fixture owned by task 11). Report disagreement 2 states the 4 correctly and the docstring was not
  updated.

The underlying mutations are sound — verified by running against the real `Observations`: mutation (b)
(warning derived from `facts_document()` nulls) yields **1** finding, mutation (c) (per null
observation) yields **4**, the shipped code yields **3**, and the three findings are exactly
`(00_baseline, fact_b)`, `(00_baseline, fact_c)`, `(01_variant, fact_c)`. The flaky case is genuinely
instantiated: `fact_b` under `00_baseline` and `fact_c` under `01_variant` each answer once and return
`null` once, and mutation (b)'s 1-against-3 is precisely the *"silent for exactly the flaky case"*
reading the null rule exists for. **The number is fixture-derived, not adjusted to fit** — I recomputed
it from the fixture's own calls rather than from the report.

---

### Minor 1 — the `condition_dir_name` import cannot be pinned, and nothing says so

`src/publishable/apparatus.py:278–287`; `tests/test_apparatus.py:434`.

The brief's Step 1 says *"import it rather than formatting the string a second time"*, and the
docstring repeats it. **Verified by running:** `sweep.condition_dir_name` is exactly
`f"{index:02d}_{label}"` (`src/publishable/sweep.py:749`) with no sanitisation, and
`condition_key(i, l) == f"{i:02d}_{l}"` for every index 0–100 across six label shapes including
`method=pearson` and the empty string. So a mutation replacing the call with an inline f-string has
**two branches that cannot differ** — the class the plan's own self-review says must be named rather
than dressed up. To be exact about what the test does pin: `:437`'s `== "00_baseline"` **does** catch a
build returning the bare label, which is what Decision 9 said before correction 2 overrode it. The one
property that cannot be pinned is the *import itself*, and the report presents it as a delivered
property without recording that no mutation can exist for it. Additionally, `tests/test_apparatus.py:437` asserts the hard-coded literal
`"00_baseline"`, where the plan's global constraint names *a condition key* among the derived values a
test must recompute; `condition_key(0, "baseline") == condition_dir_name(0, "baseline")` would at least
express the intent.

The no-sweep half **is** pinned and its stated ground is true — verified by running:
`json.dumps({None: 1, "00": 2}, sort_keys=True)` raises
`TypeError: '<' not supported between instances of 'str' and 'NoneType'`, and the rendered key sorts
(`json.dumps({condition_key(0, None): {...}}, sort_keys=True)` → `{"00": {...}}`).

### Minor 2 — a false claim about fixture adequacy, in code and in a docstring

`src/publishable/apparatus.py:227–229` — *"A build that kept the LAST observation instead cannot be
told apart from this one by any fixture with fewer than three observations"* — and the same claim at
`tests/test_apparatus.py:301`. Verified by construction: two observations `r1` then `r2` give
first-answered `r1` and last `r2`, and `r1` then `None` distinguishes first-answered from last-seen.
The three-observation fixture is fine; the argument for needing three is wrong. Delete the clause.

### Minor 3 — a cited ground the cited code qualifies

`src/publishable/apparatus.py:298` cites *"a failed execution never stops the run
(`runner.execute_plan`'s `except Exception` comment says so)"*. `runner.execute_plan` also `break`s
when `max_failed_fraction` is exceeded (`src/publishable/runner.py:741–745`), which the unqualified
sentence does not admit. The ordering argument survives the qualification — the append happens after
the result either way — so this is a wording defect, not a placement defect.

### Minor 4 — nothing rules `append_observation` against `check_facts`, and the docstring states no precondition

`src/publishable/apparatus.py:290` (`append_observation`) writes `dict(facts)` verbatim to disk with no
check of its own. Decision 6's ruled property is that a credential-carrying fact is *"not recorded"*,
but **no decision orders the append against `check_facts`** — Decision 9 rules the append's position
only relative to *the execution* it precedes. A batch-3 author wiring the ledger line ahead of the
check therefore puts a credential on disk while still satisfying every stated ordering rule, and the
docstring names no precondition on `facts`. This is the same *two mechanisms, and the ordering decides
the leak* shape Decision 5 spent a paragraph on for the credential check against the scalar walk.
**Hand-forward to batch 3:** either `append_observation`'s docstring states that its `facts` must be a
`check_facts` return, or the gap is filed in `spec-defects.md` with batch 3 as owner. Cheapest to
settle now, while no call site exists.

### Minor 5 — fact **keys** are not credential-checked, and one is interpolated into a refusal

`src/publishable/apparatus.py:163` checks values only; `coercion._refuse`
(`src/publishable/coercion.py:224`) interpolates `{key!r}`, and `check_facts` re-codes that message
verbatim at `:177`. A probe returning `{<a credential value>: [1, 2]}` therefore puts a credential into
an `E-APPARATUS-FACT-TYPE` message. Decision 6's letter is *"a fact **value**"*, so this is within the
ruling; batch 3's redacting `Collector` is what would contain it. **Recommend a `spec-defects.md`
filing rather than a code change here** — changing it silently would put a second answer beside
Decision 6's stated set.

---

## Enumerated by reading first, then confirmed by grep — every site in this batch where a fact or a probe exception can reach a stream

Read `src/publishable/apparatus.py` end to end, listed the sites, then confirmed with
`grep -n 'f"' src/publishable/apparatus.py` and `grep -n '{value\|{cred_value\|{facts\|{returned'`
(the latter returns nothing).

| Site | What it can carry | Status |
|---|---|---|
| `check_facts` `E-APPARATUS-RETURN` (×3, `:145`, `:152`, `:159`) | type names only | clean |
| `check_facts` `E-APPARATUS-FACT-CREDENTIAL` (`:168`) | fact key + variable **name** | clean, pinned by `:270` |
| `check_facts` `E-APPARATUS-FACT-TYPE` (`:177`, via `coercion._refuse`) | fact key (`{key!r}`) + type name, never the value | Minor 5 |
| `check_facts` `E-APPARATUS-FACT-MISSING` (`:182`) | declared key from the template | clean |
| `observe_once` `E-APPARATUS-RAISED` (`:124`) | the probe's own `{exc}`, **un-redacted by design** | correct per Decision 6; the redaction is batch 3's and is **not verifiable here** |
| `observe_once` `KeyboardInterrupt` (`:122`) | nothing — `str(exc) == ""` | clean, verified by running |
| `warn_unanswered` (`:271`) | condition key, fact **name**, two counts — no fact values | clean, verified by running |
| `append_observation` (`:313`) | `dict(facts)` verbatim, to disk | no check of its own and **no ruled ordering against `check_facts`** — Minor 4 |

`grep -rn "E-APPARATUS\|W-APPARATUS"` over `README.md` and the three `docs/` documents returns
**nothing**, and `grep -rn "W-ENV-UNLOCKED" src/` confirms there is no src-side warning-code registry a
new code would have to be added to — every warning code in this repo is a string literal at its emit
site. The § Errors and § Warnings rows are task 16's, as planned, and **no docstring or test in
this batch asserts a row exists.** That is the batch-1 defect not repeated.

## The batch's defining constraint, verified

- **No call site.** `grep -rn "observe_once\|check_facts\|append_observation\|Observations\|condition_key\|warn_unanswered\|facts_document\|unobserved" src/` outside `apparatus.py` → **empty**.
  `src/publishable/cli.py:3455` still writes `"apparatus": None` unconditionally.
- **`git diff --stat 307c3b3..HEAD`** touches four files: the batch report, `docs/reference.md` (+1),
  `src/publishable/apparatus.py`, `tests/test_apparatus.py`. (The diff header's fifth file,
  `progress.md`, is batch 1's fix-round entry, already committed at `307c3b3`.)
- **Decision 5:** no `__post_init__` and no validation in `Apparatus` — `grep -n "post_init"` finds only
  the docstring citing `Unit`'s.
- **Counts:** `grep -rn "unblock\|executable\|no remaining core-side"` over the report, the ledger and
  both changed source files finds only the pre-existing batch-1 ledger lines, which say zero / six /
  three, unmoved.

## Documents and gates

`docs/reference.md`'s one added line sits in § How artifacts are organized' tree at comment column 48,
identical to all nine sibling rows; `see "The apparatus files"` matches the tree's own citation style
elsewhere in the file; no trailing whitespace, tab or invisible unicode; `×` is used where the batch
multiplies. A mechanical pass over the four documents (heading-anchor uniqueness, every relative link
and `#anchor`, trailing whitespace/tabs, fenced blocks skipped) reports one hit,
`docs/reference.md` *"units.pred, units.truth"*, which is prose parenthesis matched by the link regex
and is not on a line this batch touched. No count phrase near the tree enumerates its rows.

Gates, all run directly in the foreground at `6df82fe` with `__pycache__` cleared:

- `uv run pytest` → **2392 passed, 1 skipped, 2 xfailed** in 144.80 s — matches the report exactly
- `uv run ruff check .` → All checks passed!
- `uv run ruff format --check .` → 82 files already formatted
- `uv run mypy` → Success: no issues found in **46** source files

## What I could not check

1. **The redaction half of attack point 1.** There is no call site in this batch, so *a raising probe's
   message is redacted before it reaches a stream* is not testable here — `observe_once` deliberately
   carries the message intact, which I verified by running (`E-APPARATUS-RAISED | probe `p` raised
   RuntimeError: token=lab7`). Batch 3 owns the pin; **do not read this review as evidence it holds.**
   The *returned*-credential half I did verify by running, and it refuses.
2. **The § Errors and § Warnings rows for all five codes and `W-APPARATUS-UNANSWERED`.** Task 16's, not
   yet written; absence is correct here.
3. **A no-sweep run's ledger keys through a real `run`.** No call site exists, so I verified the
   property at the function — the rendered key is `"00"` and sorts under canonical JSON — rather than
   end to end.
4. **Whether `progress.md` should already carry a batch-2 entry.** It carries none; on batch 1 the
   ledger entry landed with the *review* commit, so this appears to be the intended sequence rather
   than an omission. The two mutation adjudications and the four findings above belong in it.
