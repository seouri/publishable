# Whole-branch fix report — H7a, project-local templates

Branch `h7a-local-templates`, five commits on top of `6468842`.
All three Importants and all five Minors closed. No ruling was contradicted by the code.

| Commit | Finding |
|---|---|
| `6d2de98` | I1 — one merge per `validate` |
| `6d5822e` | I3 — fixtures that can see an order |
| `b4941e6` | I2 — a load fault preempts the collision verdict |
| `8403a6b` | M3 — drain on the no-`templates/` path |
| `761838f` | M1, M2, M4, M5 — prose and docstrings |

**Suite: 1689 passed + 2 xfailed** (baseline 1684 + 5 new). `ruff check .` and `mypy` clean, both
re-run at the final tree. `ruff format --check` compared file-by-file against `6468842` for the six
files this round touched: the same four fail live as at baseline (`validate.py`,
`generators/experiment.py`, `tests/test_templates.py`, `tests/test_validate.py`) and the same two
pass (`templates/registry.py`, `templates/discovery.py`) — no file was newly unformatted, and
nothing was reformatted.

---

## I1 — one discovery per `validate`

Shape taken: `registry.resolve_template(name, repo_root) -> (BaseTemplate | None, list[str])`,
one `_merged` for both halves; `unknown_template_message(name, known)` now takes the resolved
names. `validate` and `generate_experiment` call it inside their existing guard and pass `known`
to the message. `get_template` and `template_names` are unchanged, so the ~25 other call sites
and `cli.py` are untouched.

The single-source property survives: one function still owns the wording, and
`test_generate_experiments_unknown_template_message_matches_validates` still asserts the two live
outputs equal each other. Mutated (a trailing space at the `generate_experiment` raise) — the
live-equality assertion fails.

`tests/test_validate.py::test_a_template_cross_field_rule_is_reported` monkeypatched
`validate_mod.get_template`, which the refactor would have made a **no-op patch that passes
vacuously against the real `generic`**. Repointed to `resolve_template`; proved it still bites by
making `RuleBreaker.validate` return `[]` and confirming the test fails.

Two new tests:

- `test_one_validate_discovers_local_templates_once_on_the_unknown_name_path` — counts calls by
  wrapping (not replacing) `registry.discover_local`, which is the patch target that fires since
  `registry` imported the name. Asserts 1 on the unknown-name path and 1 on the resolvable one as
  the control. **The count is the assertion.**
- `test_a_template_whose_import_is_not_idempotent_survives_an_unknown_name` — a `templates/*.py`
  refusing a second import via a sentinel file, plus an unknown `experiment_type`; asserts
  `validate_config` returns the unknown-name finding rather than raising. This catches the class
  rather than the path: a future third caller that re-enters discovery fails it too.

Both mutations confirmed (restoring `template_names(repo_root)` inside the message call site: the
count reads 2, and the second test dies with `ContractError · E-TEMPLATE-LOAD` escaping
`validate_config`). Reverted by editing back, verified by behaviour.

## I2 — a load fault preempts the collision verdict

The claim was removed from all three sites and, per the ruling, replaced with the preemption
stated plainly plus the partial-claims reason that justifies it.

**A fourth site the review did not name**, one paragraph above the quoted one in the same
docstring: `discover_local`'s "Import order therefore never decides which template wins; both are
found and the collision is named" — false under a load fault for the identical reason. Qualified.

I also added a clause to `reference.md`'s `E-TEMPLATE-COLLISION` row saying a load fault in the
same directory preempts that code, since that is where a reader looking the code up needs it.
Rows located by what they do, never by position; pipe counts unchanged (3 per row, 2 columns).

I did **not** use the review's proposed replacement ("the collision is still computed over a
complete set of claims"). Under a load fault no collision verdict is computed at all — the claims
are collected and then not used — so that phrasing is the same both-properties-at-once error one
step removed. The text now says what eagerness buys (no well-formed template is silently skipped)
separately from what the ordering costs (no collision is reported until the directory loads clean).

`README.md`, `design-principles.md` and `experimental-designs.md` contain no `collision` prose at
all, so no sibling copy of the claim exists there.

## I3 — fixtures that can see an order

Fixture content fixed first, then the assertions.

- `test_the_colliding_name_reported_is_the_first_in_name_order` — **three** colliding names, not
  two. Two cannot separate the two wrong answers: with two names, the reverse of the insertion
  order *is* the sorted order for one arrangement, so my first two-name attempt left
  `reversed(list(claims))` green. Claimed in the order `zzz`, `aaa`, `mmm`, the reported name is
  `zzz` under insertion order, `mmm` under its reverse, `aaa` under name order.
- `test_the_broken_file_reported_is_the_first_in_the_sorted_walk` — two broken files,
  `aaa_broken.py` and `zzz_broken.py`.

Four mutations run in `discover_local` and each confirmed FAILING, then reverted by editing in
place (file diffed byte-identical to a pre-mutation copy, suite re-run green):
`sorted(claims)` → `reversed(list(claims))`; → `list(claims)`; `glob("*.py")` →
`glob("*.py"), reverse=True`; `raise load_faults[0]` → `load_faults[-1]`.

## Minors

- **M1** — confirmed against `hashes.py` before writing: `__pycache__` is skipped as a directory
  part and `.pyc`/`.pyo` as suffixes, unconditionally, and `code_hash` reads the working tree. The
  two mechanisms are now separate sentences, and the follow-on says the hand-assembled repo goes
  dirty *while its `code_hash` is unchanged*. Behaviour described, private symbol not named in
  normative prose.
- **M2** — `| Template is installed |` → `| Template resolves |`. The example cell is still
  accurate for the plugin case and was left alone.
- **M3** — `drain_pending()` moved above the `is_dir` early return, and the docstring promise
  extended to say it holds on every path out.
  **One correction to the review's diagnosis:** the stated harm ("a stale registration queued for
  the *next* repo's discovery to inherit and misattribute") is not reachable — the next
  `discover_local` drains at the top before its own loop, so the stale entry is discarded either
  way, which is why my first test passed under the mutant. The real defect is the unconditional
  promise over a conditional path, i.e. the buffer left dirty for whatever drains next. The test
  therefore asserts the buffer directly (`drain_pending() == []` after a no-`templates/` call),
  which *is* the promise rather than a proxy for it, with the empty mapping as the control and a
  `finally` drain so the module-level buffer cannot poison the session. Mutation (drain back below
  the return) confirmed failing.
- **M4** — scoped to import time, and the docstring now says the path is restored before any
  template method runs. Probed rather than assumed: `importlib.import_module("__helper")` inside
  `aggregate` raises `ModuleNotFoundError: No module named '__helper'`.
- **M5** — out of scope to change; the predicate is untouched. One clause added to
  `is_local_template` naming the `src/**`-defined case as landing non-local, written as what the
  predicate does and which way it fails, not as a guarantee that it is the right answer.

## Concerns

1. **`registry._merged`'s `sorted(local)` is unfalsifiable by construction.** It carries the same
   "import order may decide nothing" reason as the collision loop, but `_BUILTIN` holds exactly
   one name, so no fixture can make a shadow-refusal order observable. Not a defect, and not worth
   a test until core ships a second builtin — recorded so the next reviewer does not re-find it.
2. **The two-name trap in I3 generalises.** A fixture with two of anything can only kill one of
   `{insertion order, its reverse}`; three distinct values are the minimum that pins a sort. Worth
   the ledger, since the suite's other ordering claims are all one-item fixtures.
3. **Nothing tests the `code_hash`/dirty-gate split M1 now documents.** The review verified both by
   hand at `6468842`; the branch still has no test that `templates/__pycache__` leaves `code_hash`
   byte-identical, which is what makes M1's sentence a documented-but-unchecked row of the kind
   CLAUDE.md warns about. Out of scope for a fix round, cheap for whoever wants it.
4. **`unknown_template_message`'s `known` argument is now a plain `Sequence[str]`,** so a caller
   could pass a list from a *different* repo root and the message would lie without any type error.
   Both call sites take it from the same `resolve_template` return; there is no third caller.
5. **`cli.py`'s own `get_template` is a third discovery on a run.** Looked at rather than left
   unchecked: it sits in the aggregate/finalize path, and `run` also calls `validate_config`, so a
   `run` performs at least two local discoveries — one inside validation, one here. Left alone
   deliberately: the I1 ruling is scoped to `validate`'s unknown-name path, `run` is not contracted
   never to raise, and this call has a resolved name rather than a message to build, so the
   `resolve_template` shape does not apply to it. Worth a ruling of its own if eager discovery ever
   gets expensive.
6. **No spec sentence was added for "one discovery per `validate`".** Judged an implementation
   property rather than a promise — § Creating a plugin's existing sentence is about *what* gets
   imported, not how often — so the durable record is `resolve_template`'s docstring, `validate`'s
   comment, and the counting test, all of which are tracked, unlike the ledger ruling task 14
   could not see. Recorded here so it is not re-litigated.
