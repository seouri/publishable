# Task 6 review: `_check_holdout`, declaration half B — `stratify_by` existence, `holdout` × `fold`

**Reviewed:** `8f7270b..b5d1ae6` (two commits; `src/publishable/validate.py` +112/−13, `tests/test_validate.py` +147, plus the task report).

**Verdict 1 — Spec compliance: ✅.** Both codes are emitted from inside `_check_holdout`, `stratify_by`
is read through `units.stratum_names` rather than a hand-rolled `isinstance` chain, one finding is
reported per offending name, the fold exclusion is sited here reading `replication.repeats` (and
`replication.py` is untouched, so `REPL_DECLARATION_CODES` is unchanged as the brief required), and the
docstring enumeration grew from five to seven. The single deviation from the brief's literal test text is
a *strengthening* the implementer diagnosed correctly: the brief's mutation 5(a) does not discriminate,
because the test read only a count. That is the behaviour this process wants, and the report states it
plainly.

**Verdict 2 — Task quality: ❌.** Two findings. One whole branch of
`E-DATA-HOLDOUT-STRATIFY-UNKNOWN` is deletable with the **full** suite green, and half of that branch has
no fixture at all (F1). And `reference.md` § Errors now contradicts itself about
`holdout.stratify_by: []` — row 480 says it is not refused, row 482 says it is, and this commit is what
made row 480 false (F2). Both are narrow, named fixes. This task is materially better than task 5: the
implementer found and closed the count-blindness that the brief *and* the controller's pre-dispatch check
both missed.

## Verification baseline

- Working tree at `b5d1ae6`. `uv run pytest` → **1857 passed, 2 xfailed** (matches the report).
  `uv run ruff check .` → clean. `uv run mypy` → clean. `uv run ruff format --check --diff
  tests/test_validate.py` → one hunk (`@@ -11550`), exactly the one line the report declares.
- Every mutation below was applied by rewriting the file's text in place (never `git checkout --`), with
  `__pycache__` deleted before each run, and each revert verified by **re-running** the named tests plus
  `diff -q` against a pre-mutation copy (final state: `IDENTICAL`, 35 holdout tests passing).
- `.superpowers/sdd/.gitignore` was found clobbered to a bare `*` again; restored from `HEAD`.
  `git status --porcelain` empty afterwards.

### Mutation table — what each branch is discriminated by

| Production mutation | Expected killer | Result |
|---|---|---|
| `if raw_strata is not None and not strata:` → `if False:` | the `""` and `[]` parametrize rows | **2 failed** |
| `if name not in declared_names:` → `if False:` | the two-undeclared-names test, the bare-string test | **2 failed** |
| `if name not in declared_names:` → `if name in declared_names:` | the positive `_accepted` test as well | **3 failed** |
| `if isinstance(measurement_axis, str) and measurement_axis == name:` → `if False:` | the measurement-axis test | **1 failed** |
| `level.get("kind") == "fold"` → `"batch"` (brief's 5(b)) | the fold test | **1 failed** |
| `level.get("kind") == "fold"` → `is not None` | the seed control | **1 failed** |
| **`if not isinstance(name, str) or not name:` → `if False:`** | **nothing** | **1857 passed** — F1 |

---

## Important

### F1 — The non-string/empty-name branch is invisible to the whole suite, and half of it has no fixture

**Verified by mutation, full suite:** replacing `if not isinstance(name, str) or not name:` with
`if False:` leaves `uv run pytest` at **1857 passed, 2 xfailed** — the same count as the unmutated tree.
The branch can be deleted outright and nothing notices.

The reason is exactly the shape the controller's own pre-dispatch failure illustrated, one branch over:
the four parametrize rows `["", [], 7, [3]]` assert only that the *code* appears. With the branch gone,
`7` and `[3]` fall through to the `name not in declared_names` branch, which reports the **same code at
the same path** with a different message ("names 7, which is not a unit attribute …" instead of "names 7,
which is not the name of a unit attribute — a split is balanced on attributes named as strings"). Code
and path are identical across all three branches, so the message is the only observable, and only the
bare-string test observes one.

**A sub-gap the diff does not reach at all.** The branch has two clauses and one of them has no fixture:

- `not isinstance(name, str)` — reached by `7` and `[3]`.
- `not name` — reached **only** by `stratify_by: [""]`. `stratum_names([""])` returns `("",)` (the list is
  truthy, so the *empty-declaration* gate never sees it) and `""` then trips `not name`. **Verified by
  probe:** `[""]` → `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`, message `names '', which is not the name of a unit
  attribute — a split is balanced on attributes named as strings`. No test in the diff writes `[""]`;
  row 482's "an empty string" is read by the fixtures as the scalar `""`, which takes a *different*
  branch. The assign sibling (row 473) names `[""]` explicitly, so this is a case the repo has already
  decided is real.

**Constraint on the fix.** The obvious remedy — add a message assertion to
`test_a_holdout_stratum_that_names_no_attribute_at_all_is_refused` — cannot work as written: its four
params straddle two branches with two different messages (`""`/`[]` → "is empty …"; `7`/`[3]` → "names …
not the name of a unit attribute"). One message assertion over all four is either false or blind again.
Parametrize the expected message fragment alongside the value (or split the test in two), and add a
`[""]` row. `messages_by_code` already exists in the same file.

### F2 — `reference.md` § Errors now contradicts itself about `holdout.stratify_by: []`

**Verified by probe:** `{"method": "by_attribute", "from": "split", "stratify_by": []}` →
`E-DATA-HOLDOUT-STRATIFY-UNKNOWN` (+ `E-DATA-HOLDOUT-UNSUPPORTED`). `{"method": "random", "frac": 0.2,
"stratify_by": []}` → the same code.

- § Errors, `E-DATA-HOLDOUT-NO-DRAW`: "… including its `!= []` exemption — an empty `stratify_by: []`,
  what `init` writes, changes no behavior **and is not refused**."
- § Errors, `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`: "… or is not the name of an attribute at all: a
  non-string, an empty string, **or an empty list**."

Both rows are in the same table, both about `data.units.holdout.stratify_by`. The sophisticated reading
("not refused *by this row*") should be rejected: CLAUDE.md's own misreading table exists because readers
take a row's wording as its scope, and a reader writing a holdout config from the NO-DRAW row will
conclude `[]` is fine. It is not — the block is refused.

**Ownership is this task's.** The NO-DRAW row's clause was true when it was written: the task-5 review
fix exempted `[]` from NO-DRAW and nothing else refused it (confirmed by the probe above — `[]` under
`by_attribute` no longer earns `-NO-DRAW`). **This commit is what falsifies it**, the "a sentence derives
its claim from a state that changed" shape the cross-document pass names. The code follows row 482, so
this is a document defect: one clause in the NO-DRAW row (e.g. "not refused *here* — an empty list is
`E-DATA-HOLDOUT-STRATIFY-UNKNOWN`'s own row"). Note also that `init` writes `holdout: null`, so "what
`init` writes" is imported wholesale from the assign sibling and is not true of this block either.

---

## Minor

### F3 — "seven findings … in declaration order" is false under the field-order reading

`reference.md` § A fixed holdout split declares `method, frac, from, stratify_by, seed`, so
`stratify_by` **precedes** `seed`; the docstring lists `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` after
`E-DATA-HOLDOUT-SEED`. It is true under an emit-order reading. Task 5's five were true under *both*
readings, which is why the phrase read as settled; this task is where the two diverge. Inherited from the
brief's prescribed insertion point. Either say "in emit order" or move the bullet.

### F4 — The empty-branch comment is narrower than the code

```python
        # An empty string or an empty list: present, and naming nothing.
```

**Verified by probe:** `stratify_by: 0`, `stratify_by: false`, and `stratify_by: {}` all take that branch
and get the message "is empty, which names no attribute to balance the split on …". `{}` is fair; `0` and
`false` are not "an empty string or an empty list", and "is empty" is a slightly wrong thing to say about
`0` when a `7` one line down is told it "is not the name of a unit attribute". Category (b) — a comment
claiming a narrower rule than the code implements. Cheapest honest fix is the comment ("anything
`stratum_names` normalizes to no names").

### F5 — Row 482's roster-independence claim is correct but unpinned

Row 482 states "Checked from the declaration alone, so it reports whether or not a roster resolved."
**Verified by probe** (config with no `index.csv` written): `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` still fires
alongside `E-UNITS-ATTR-MISSING`. Correct — but every stratify test in the diff writes a resolvable
roster, so nothing pins it. One assertion on an unresolvable roster would.

### F6 — `units.stratum_names`'s docstring is stale, and this task did not own it

It says "**Public, and imported by `validate._check_assign` and `validate._check_resample`**". There are
now four `validate` call sites (`_check_assign`, its NO-DRAW read, `_check_fold_stratify_by`,
`_check_holdout`) plus `cli.py` and `units.py`. **Verified by grep** (`grep -rn "stratum_names" src/`).
It was already stale before this commit (`_check_fold_stratify_by` at `validate.py:5413`), the design's
flagged docstring is `stratum_varies_within_cluster`'s (owned by the later `-STRATIFY-VARIES` task), and
this brief said nothing about it. **Observed, not owned** — recorded so the next reviewer does not
re-derive it. Its H4a paragraph ("still not wired — check `cli.command_run` directly") also now has an
answer: `cli.py:1122` calls `stratum_names` on the resample declaration.

---

## Checked and correct

- **(c) The fold exclusion degrades rather than raises.** `(doc.get("replication") or {}).get("repeats")`
  is the file's convention at 23 sites. **Verified by probe:** `replication` as `"x"`, `7`, or `["a"]`
  never reaches `_check_holdout` at all (no `E-DATA-HOLDOUT-*` code is emitted — the envelope's type
  finding stops the pass first), so the `.get` on a non-mapping is unreachable; `{"repeats": "fold"}`,
  `{"repeats": [7]}` and `{"repeats": None}` all degrade silently through the two `isinstance` guards. No
  crash, no finding.
- **Diagnostic completeness, verified independently of the report.** § Errors row for
  `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` covers all **four** emit sites this diff creates — the empty
  declaration, the non-string/empty entry, the undeclared name, and the measurement axis ("a non-string,
  an empty string, or an empty list" absorbs the first two). The `E-DATA-HOLDOUT-FOLD` row covers its
  single site. § Validation carries *Stratification attribute exists* (naming the `holdout` half and the
  `measurements.by` case) and *One evaluation split, not two*. **"No document change needed" holds** —
  F2 is about a *different* row.
- **Alongside, never instead of. ✅** Every new test asserts `E-DATA-HOLDOUT-UNSUPPORTED` on its own line
  with `in`; no test asserts a total set of codes. Task 17/18's retirement is a one-line deletion per
  test.
- **Task 5's F5 was not reintroduced under `-NO-DRAW`.** `[]` under `by_attribute` no longer earns
  `E-DATA-HOLDOUT-NO-DRAW` (probe above). The `[]` refusal this task adds is a *different* code with its
  own § Errors row — legitimate behaviour, F2 is only about the sibling row's stale sentence.
- **The wrong-typed container is absorbed here rather than skipped**, unlike `_check_resample` (which
  nulls a non-`(str, list)` container to avoid doubling `E-CONFIG-TYPE`). Probe: `stratify_by: {a: 1}` →
  `E-CONFIG-TYPE` **and** `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`. That divergence is what row 482 specifies
  ("a non-string … at all") and what the brief argued for, so it is deliberate, not a defect.
- **One finding per offending name is actually pinned**, not just counted: the two-name test joins the
  messages and asserts both `'sex'` and `'cohort'` appear, so a loop reporting `strata[0]` twice fails.
- **The comment's sibling claim** that `data.units.attributes` is the reference set "`_check_cluster_by`,
  `_check_weight_by` and `_check_fold_stratify_by` all read" — verified by reading all three; each reads
  the declared attribute list rather than the roster's columns.
- **`replication.py` untouched**, as the brief required for task 18's retirement.
