# Task 3 report: registry takes an optional repo root, merges per call

## What changed

`src/publishable/templates/registry.py` rewritten:

- `get_template(name: str, repo_root: Path | None = None) -> BaseTemplate | None`
- `template_names(repo_root: Path | None = None) -> list[str]`
- New private `_merged(repo_root)` builds `{**discover_local(repo_root), **_BUILTIN}` fresh on
  every call when `repo_root` is given, or just `dict(_BUILTIN)` when it isn't. No module-global
  cache — verified by mutation (see below).
- **Merge direction: core wins.** A local template named `generic` cannot shadow the built-in;
  it is resolved by name, never by load order, per `design-principles.md`'s registration
  invariant (a collision or shadow of a core name fails at load / is not resolved by install
  order). This is a judgment call the brief didn't pin down explicitly — flagging it for review
  in case shadow-with-diagnostic was intended instead of silent core-wins.

`tests/test_templates.py`:
- Added `test_a_local_template_resolves_by_name`, `test_without_a_repo_root_only_builtins_resolve`,
  `test_template_names_includes_locals_and_stays_sorted` (as specified in the brief), plus two
  more the brief's own examples didn't cover (see "What I decided" below):
  `test_a_repo_root_does_not_fabricate_an_unknown_name` and
  `test_per_call_merge_does_not_leak_between_two_roots`.
- Existing `test_an_unknown_template_is_not_resolved` (`get_template("llm_diagnostic") is None`,
  no root) left unchanged.

`tests/test_materialize.py` and `tests/test_validate.py`: **no edits needed.** Both call
`get_template("generic")` / the monkeypatch lambda takes one positional argument; since
`repo_root` defaults to `None`, single-positional-arg calls remain valid Python and valid
behaviour. The suite collects and passes without touching either file. See "Discrepancy from
the brief" below.

## What I decided `get_template("llm_diagnostic") is None` still means

Left as-is with no root: it now reads as "with no repo root, the closed builtin set doesn't
include this name" — a narrower, still-true claim than before, but on its own it's subsumed by
`test_without_a_repo_root_only_builtins_resolve` (same claim, weaker).

What still has independent content is a *different* assertion I added:
`test_a_repo_root_does_not_fabricate_an_unknown_name` asserts
`get_template("llm_diagnostic", tmp_path) is None` **with a real local template
(`real_one`) defined in that same `tmp_path/templates/` as the control that must resolve.**
That's the meaning worth keeping: a repo root does not invent names it was never given — a
discovery that silently returned `{}` for everything would fail this test (both assertions),
not just look unremarkable.

## The dimension the brief's own test list couldn't see

Per-call merging (no module-global cache) is this task's actual requirement, but none of the
three tests in the brief's Step 1 can distinguish per-call merge from a cache built on first
call — each of them uses at most one repo root per test process/test function. I added
`test_per_call_merge_does_not_leak_between_two_roots`: two roots in one test, `alpha` defined
only under `root_a`; asserts `get_template("alpha", root_a) is not None` and
`get_template("alpha", root_b) is None`. Confirmed this fails under a module-global cache (see
mutation log below) and passes under the per-call implementation.

Also fixed a near-tautology risk in `test_without_a_repo_root_only_builtins_resolve`: the brief's
example never writes `tmp_path/templates/my_assay.py`, so `get_template("my_assay") is None`
would pass whether or not the root argument gated discovery at all. My version writes the file
first, so the assertion is genuinely about the missing root argument, not about the file being
absent.

## Mutation testing (verified by behaviour, not `git status`)

1. **Return locals only** (`return discover_local(repo_root)`, drop `_BUILTIN` from the merge):
   ran `test_a_local_template_resolves_by_name` — FAILED
   (`assert get_template("generic", tmp_path) is not None` → `None is not None`). Deleted
   `__pycache__`, reverted, reran — PASSED.
2. **Cache the merged mapping module-globally** (`_cache` global, populate once, return
   thereafter): ran `test_per_call_merge_does_not_leak_between_two_roots` — FAILED
   (`get_template("alpha", root_b)` returned the `Alpha` instance leaked from `root_a`'s call).
   Deleted `__pycache__`, reverted, reran — PASSED.

## Discrepancy from the brief

The brief and the task instructions both describe "six call sites" / "three test bindings"
needing edits so the suite doesn't fail collection. Checked empirically: `repo_root` is optional
with default `None`, so every existing single-positional-arg call
(`get_template("generic")` ×2 in `test_materialize.py`,
`lambda name: RuleBreaker()` in `test_validate.py`, and the three in `test_templates.py`)
remains valid both syntactically and behaviourally. I ran
`uv run pytest --collect-only tests/test_templates.py tests/test_materialize.py
tests/test_validate.py` before making any changes — 596 tests collected cleanly, no signature
break. I did not manufacture edits to those two untouched files to match the brief's narrative;
reporting this as a finding instead. The `test_validate.py` lambda would only actually need its
signature to accept `repo_root` once a later task (4, per the brief) hoists `repo_root` into
`validate.py`'s own call site — that hasn't happened here.

## Verification

- `uv run pytest` — 1647 passed, 2 xfailed
- `uv run ruff check .` — all checks passed
- `uv run mypy` — no issues, 41 source files
- `ruff format .` not run, per instructions

## Round 2: coordinator review corrections

Three fixes made in response to review; all verified, not asserted.

**1 — docstring overclaimed designed policy, and misattributed the citation.**
The original docstring said core-wins was "resolved by name, never by load order" as if that
were this task's design. Wrong on two counts: (a) `reference.md` § Creating a plugin — not
`design-principles.md`, which contains neither "collision" nor "install order" (confirmed by
grep) — requires that exact case to **fail at load, naming both providers**, and uses that same
phrase as the reason for *refusing* the shadow, not for resolving it silently; (b) a task-7
implementer reading the old docstring would take silent core-wins as spec rather than as an
interim stand-in. Rewrote the docstring: the behaviour is now marked explicitly interim, task 7
is named as the refusal that replaces it, and the citation points to `reference.md` § Creating a
plugin.

**2 — added a local-class-identity assertion; confirmed it moves.**
The reviewer's mutation — resolve every local name to core's own `GenericTemplate`
(`locals_ = {n: GenericTemplate for n in discover_local(repo_root)}`) — passed all 16 tests as
they stood, because `test_a_local_template_resolves_by_name` only checked `is not None`, never
which class came back. `test_template_names_includes_locals_and_stays_sorted` still can't see
this (it only ever sees names). Added
`assert type(resolved).__name__ == "MyAssay"` to `test_a_local_template_resolves_by_name`.
Re-ran the exact mutation: FAILED (`'GenericTemplate' == 'MyAssay'`). Deleted `__pycache__`,
reverted, reran — PASSED (16/16).

**3 — corrected a false claim in this report about test coverage.**
I had written that none of the brief's three Step-1 examples can distinguish per-call merge from
an unkeyed module-global cache. Reviewer mutation-tested this and it's wrong:
`test_template_names_includes_locals_and_stays_sorted` calls `template_names(tmp_path)` then
`template_names()` in the same test — two different `repo_root` values in one process — so it
already fails under an unkeyed cache on its own. Reproduced independently: applied the exact
`_cache` mutation from mutation-log item 2 above and ran only
`test_template_names_includes_locals_and_stays_sorted` — FAILED
(`['generic', 'my_assay'] == ['generic']`, the leaked-in `my_assay` still present on the
root-less call). Deleted `__pycache__`, reverted, reran — PASSED.

Corrected claim: `test_template_names_includes_locals_and_stays_sorted` already covers the
`None`-vs-non-`None` root case for an unkeyed cache. What it does **not** cover, and what
`test_per_call_merge_does_not_leak_between_two_roots` is the only cover for, is leakage between
two *non-`None`* roots (`root_a` vs `root_b`, both with local templates) — a case an unkeyed
cache also breaks but that none of the brief's three examples exercise even incidentally. Kept
that test; the earlier "none of the three can see this" framing is retracted as stated and
replaced with the narrower, correct claim above.

Also noted for the record, per the coordinator's routing (no action taken here): task 4's brief
will need to record that `test_validate.py`'s one-argument monkeypatch lambda breaks loudly, not
vacuously, the moment `validate.py` itself calls `get_template(name, repo_root)`; and task 7's
brief will need `registry.py` in its file list, both because importing `_BUILTIN` into
`discovery.py` would be circular in either direction, and because `discover_local` currently
drops the first provider silently on a local × local name collision, which the refusal in
finding 1 above needs surfaced with a claiming path per name.

### Round 2 verification

- Reproduced both review-cited mutations directly (local-identity swap; unkeyed module-global
  cache) against `test_a_local_template_resolves_by_name` and
  `test_template_names_includes_locals_and_stays_sorted` respectively — both FAILED as the
  reviewer stated. Deleted `__pycache__` after each, reverted, reran — both PASSED.
- `uv run pytest` — 1647 passed, 2 xfailed
- `uv run ruff check .` — all checks passed
- `uv run mypy` — no issues, 41 source files
