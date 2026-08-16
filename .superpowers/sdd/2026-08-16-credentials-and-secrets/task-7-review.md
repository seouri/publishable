# Task 7 — review

Reviewed `60ee96b..b907ab6` (commit `b907ab6`, "feat: secrets.py — .env loading, the values core
read, and redaction by exact value") on branch `h7c-credentials`. Diff touches
`docs/reference.md` (1 line), `pyproject.toml`, `uv.lock`, and adds `src/publishable/secrets.py`
and `tests/test_secrets.py`.

## Verdicts

| | Verdict |
|---|---|
| **Spec compliance** | ✅ |
| **Task quality** | ❌ — one normative guarantee has no check that can fail (Important 1) |

Baseline re-measured myself: `uv run pytest -q` → **1971 passed, 2 xfailed** (matches the brief).
`uv run mypy` → clean, 43 source files, **no `dotenv.*` override present or needed**.
`uv run ruff check .` → clean. `uv run ruff format --check .` → **76 files already formatted**.
All mutations reverted by editing files back; working tree confirmed byte-identical to `b907ab6`
by `git diff HEAD -- src/ tests/ docs/ pyproject.toml uv.lock` (empty) and by re-running the suite,
never by `git status` alone.

---

## Findings

### Important 1 — `missing_env`'s declared-order guarantee has no check that can fail

`reference.md` § Validation's `E-CRED-MISSING` row makes the order normative: *"One finding per
unset variable, **in the order the list declares them**, so a template needing three keys names all
three rather than one at a time."* The docstring repeats it: *"Declared names with no value, **in
declared order**, each named once."*

**Mutation run:** `return out` → `return sorted(out)` in `missing_env`.
**Result: `7 passed`.** The guarantee is not pinned.

The cause is CLAUDE.md's named trap, *a fixture with too few elements to distinguish the candidate
orderings*: the fixture's names are `PUBLISHABLE_TEST_OTHER` and `PUBLISHABLE_TEST_THIRD`, and
`O < T`, so **declared order and sorted order are the same list** for this fixture. I confirmed the
test is not vacuous in general — `return list(reversed(out))` **does** fail it — so what the test
actually pins is *"not reversed"*, which is strictly weaker than the documented claim and is the one
mutation an implementer would think to try.

**Fix is one line:** rename a fixture name so declared order ≠ sorted order — e.g. declare
`PUBLISHABLE_TEST_ZULU` first, expect `[ZULU, OTHER]`. Then `sorted(out)` fails.

This lands on task quality rather than on the code (the implementation is correct). It is in scope
because the brief's item (a) named `missing_env` specifically, and because Step 7 asked what the
mutation set does not reach — the report answers that question only about the provenance claim, and
its *"All three discriminated correctly"* is true but not the whole answer.

**Why this is ❌ and not a Minor — it is a trap laid for the next task.** The anticipated rebuttal is
that declared order is `E-CRED-MISSING`'s *finding* order and therefore task 9's to pin. That makes
it worse, not better, and CLAUDE.md has the row: *"A test whose **name** claims the guarantee …
The name and docstring asserted an agreement no assertion made — and a reader greps for exactly
that name and stops looking."* The test is called
`test_missing_env_answers_in_declared_order_and_dedupes` and its docstring-adjacent comment claims
the dedupe control; task 9's implementer will grep for a declared-order test, find this one, and
reasonably conclude the ordering is already covered. The weaker-than-advertised test is the
mechanism by which the normative guarantee never gets a check at all.

### Important 2 — the fixture is right, but the plan's prescription it works around is false, and tasks 8–12 will repeat the leak

The implementer's report is **correct on every point** and I reproduced it. Deleting the autouse
fixture from `tests/test_secrets.py` reproduces the failure exactly as described:
`test_an_empty_string_counts_as_unset` fails with `PUBLISHABLE_TEST_TOKEN: 'from-the-file'` still in
`os.environ`. The leak is real and predates the implementation.

I also verified the fixture restores **faithfully in both directions**, which the brief asked for
specifically. I appended four probe tests to a copy of the file (in `tests/`, so the real autouse
fixture applied) that delete a pre-existing variable and set a new one *directly*, bypassing
`monkeypatch` entirely — all passed with the fixture, and **I proved the probes can fail** by
removing the fixture, at which point the delete-restore and set-removal probes both failed. So
`dict(os.environ)` + `clear()` + `update()` restores deletions, not only additions. Fixture teardown
also orders correctly relative to `monkeypatch` (autouse sets up first, tears down last, so the
snapshot predates any `monkeypatch` change). Probe files removed; `tests/` is clean.

**The additive finding:** the plan's own global discipline (`docs/superpowers/plans/2026-08-16-credentials-and-secrets.md`,
§ traps, the `load_dotenv` writes straight into `os.environ` paragraph) prescribes a remedy that
does not work:

> *"Before triggering any load, call `monkeypatch.delenv(NAME, raising=False)` for every name the
> `.env` holds: `monkeypatch` records the pre-state and, since the name was absent, deletes it again
> at teardown."*

**Verified false empirically**, not from recalled source: a two-test probe where the first calls
`monkeypatch.delenv(N, raising=False)` on an absent name and then writes `os.environ[N]` directly
leaves `N` set in the second test. `MonkeyPatch.delitem` records nothing when the name is absent and
`raising=False`, so it provides no protection at all — which is precisely why task 7's own tests
leaked despite following the prescription.

Task 7's fixture is **file-local**. Tasks 8–12 add `.env`-triggering tests in `test_validate.py` and
`test_cli.py` and will follow the same false prescription, so the leak recurs there.
**Route:** an appended correction to the plan (never a retro-edit — CLAUDE.md), and/or move the
snapshot fixture to `tests/conftest.py`. Filed against tasks 8–12, not against this commit.

**This finding carries no verdict weight.** Task 7's own handling is correct and its fixture is
faithful; the ❌ rests on Important 1 alone. It is recorded here because task 7 is where the
mechanism was discovered and where the evidence lives, not because anything in this commit is wrong.

### Minor 3 — `load_env`'s docstring states a return contract the code does not provide

> *"Load `<repo_root>/.env` into `os.environ`. **Returns whether a file was read.**"*

Probed directly against the installed 1.2.3:

| Case | `load_env` returns |
|---|---|
| `.env` exists, contains `# nothing here\n` | **`False`** — file was read |
| `.env` exists, empty | **`False`** — file was read |
| `.env` exists, one binding, variable unset | `True` |
| `.env` exists, one binding, **already set in shell** (binding skipped) | **`True`** — nothing was set |

`DotEnv.set_as_environment_variables` returns `False` when `self.dict()` is empty and `True`
otherwise, regardless of whether `override=False` skipped every binding. So the value means neither
*"a file was read"* nor *"something was set"* — it means *"the file parsed to at least one
binding"*. This is CLAUDE.md's *comment claiming a guarantee the code does not provide*. Tasks 8–12
consume this return value, so it is worth correcting now rather than after a caller relies on it.

### Minor 4 — the module docstring's `provenance.environment` enumeration is a present-tense build claim that overstates today's code

The safety claim's **load-bearing direction is true, and unusually strongly so.** I verified:
`grep -rn "os.environ\|os.getenv" src/publishable/` returns **only `secrets.py`** — it is the sole
module in core that reads the environment at all. `provenance.py` reads no environment variable and
defines only `GitInfo`, `_git`, `resolves_inside_repo`, `find_repo_root`, `git_provenance`.
`secrets.py` imports `os`, `collections.abc`, `pathlib`, `dotenv` — nothing from `publishable`, and
it writes no file. So *"nothing in this module imports `publishable.provenance` or writes into the
document it builds"* is true by construction, exactly as the brief asked.

The overstatement is the next clause: *"`provenance.environment` is assembled from `os`,
`hostname`, `hardware` and `uv.lock` alone."* The block that ships today (`cli.py`, the
`"environment"` key) holds `manager`, `python_version`, `uv_lock`, `uv_lock_hash` — **no `hostname`
and no `hardware` field exists yet**. The sentence describes the *specified* shape (§ What `study
add` redacts names `provenance.environment.hostname`) in the present tense of code. Harmless to the
safety argument, but it is the shape CLAUDE.md § Feasibility analyses item 10 warns about.

### Minor 5 — `PYTHON_DOTENV_DISABLED` is a behavior-changing env var in core's load path, undocumented

`dotenv.main._load_dotenv_disabled()` short-circuits `load_dotenv` when `PYTHON_DOTENV_DISABLED` is
one of `1/true/t/yes/y` (case-folded). Probed: with it set, `load_env` returns `False` and loads
nothing. **Not a regression from the version bump** — I checked the cached 1.2.1, 1.2.2 and 1.2.3
trees and all three contain it, so the brief's 1.2.1 would behave identically.

It **fails closed** (nothing loads → `missing_env` reports → `E-CRED-MISSING`), so it is not a leak
and does not block either verdict. But CLAUDE.md's first invariant is *"no behavior-changing env
vars"*, and core's `.env` load now silently honours one it does not document. **Route:** a
`spec-defects.md` filing under task 14, which owns filings.

### Minor 6 — the brief's Step 1 confirmation command is impossible, and the report asserts the step without noting it

`uv run python -c "import dotenv; print(dotenv.__version__)"` raises
`AttributeError: module 'dotenv' has no attribute '__version__'`. No 1.2.x ships `__version__` in
`dotenv/__init__.py` (checked all three cached trees). The report lists the dependency disagreement
it *did* find (1.2.1 → 1.2.3) carefully and correctly, but records Step 1 as done without flagging
that its verification command cannot run. Lands on the report and on the brief, not on the code.

---

## Verified good — what I checked and how

**Decision 4 — redaction by exact value, no proxy.** `redact` matches with `str.replace` over values
that came from `credential_values`, i.e. values core actually read out of `os.environ` for a
declared name. There is no pattern, no entropy heuristic, no name-suffix test anywhere in the
module. The fail-closed direction is pinned by the test's `sk-zzzzzz` case — a string that *looks*
like a credential is untouched. Cannot be fooled by a look-alike, because nothing but the value set
is consulted.

**Decision 4a — respected here; its *stating* is not this task's debt.** Core can only redact what
was passed in, which is exactly the documented limit. The obligation to *say so* in the documents is
a **document-only deliverable of task 12** (plan § Task 12, *"Decision 4a is a document-only
deliverable and it belongs here"*), so its absence from task 7 is correct routing, not a gap.

**Empty and degenerate values — probed, and safe in the fail-closed direction.** Guarded twice:
`credential_values` drops empty values before they reach `redact`, and `redact`'s loop re-guards
with `if value:`. Probes: `redact("banana", {"K": ""})` → `'banana'` (unchanged — the
corrupt-every-message hazard is closed); `redact("", {...})` → `''`; `redact(None, {...})` → `None`.
A one-character credential over-redacts — `redact("banana bread", {"K": "a"})` →
`'b<redacted:K>n<redacted:K>n<redacted:K> bre<redacted:K>d'` — which is inherent to exact-value
matching and errs toward removing too much, never too little. No docstring claims otherwise, so
there is no mismatch to file.

**Mutation (a), re-run by me as instructed, with the test body checked first.** `test_a_shell_value_wins_over_the_file`
calls `monkeypatch.setenv(_NAME, "from-the-shell")` on the line *before* it writes a different value
to the file, and asserts on the resolved value — so the two branches genuinely differ. Flipping
`override=False` → `override=True` **FAILS** that test and only that test. The report's account is
accurate.

**Idempotence IS pinned — I set out to file this as vacuous and falsified my own hypothesis.**
`override=True` does not break the "twice, same answer" lines, so I ran a memoization mutation
instead (`_LOADED` guard at the top of `load_env`). Run in **isolation**, so test-order effects
cannot account for it, it fails at `tests/test_secrets.py:47` — which is exactly
`assert load_env(tmp_path) is True  # twice, same answer`. The second-call assertion is load-bearing.
No finding.

**Longest-first sort.** The report's mutation (b) is sound; the tie-break key `(-len(kv[1]), kv[0])`
is fully deterministic, so the ordering cannot vary by dict insertion order in production either.

**`credential_values` is pinned — mutation run, since the brief named it alongside `missing_env`.**
`if value:` → `if value is not None:` **FAILS** `test_an_empty_string_counts_as_unset` at
`tests/test_secrets.py:82`, the `credential_values([_NAME]) == {}` assertion. Its name→value mapping
is separately pinned by `test_a_shell_value_wins_over_the_file`'s
`== {_NAME: "from-the-shell"}`, which asserts the value and not merely the key. No gap here.

**The premise the unpinned-claim routing rests on, made explicit rather than inferred.**
`grep -rn "secrets" src/publishable/` and a grep for `load_env|credential_values|missing_env|redact(`
both return **nothing outside `secrets.py` itself**. The module is genuinely unwired at this commit,
so "no mutation in this task can reach the provenance claim" is a verified fact, not a diff-shaped
assumption.

**The marker sweep, run across the named files rather than the one the change was noticed in.**
CLAUDE.md's *"Sweep for the claim, not for the file the claim was first noticed in"* — I grepped
`secrets` and `.env` across `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md`, `CLAUDE.md` and `docs/feasibility-llm-growth-studies.md`, **filtering the file
list rather than the grep output**, and intersected with `not yet built|unbuilt|NOT BUILT`: **no
hits**. No passage anywhere still asserts `secrets.py` or `.env` loading is unbuilt — including
§ CLI reference's `Status` column and § The importable surface, which task 6 had just touched.
`secrets.py` appears in `reference.md` at exactly one line, 3611, the edited one. Sweep proven able
to fail against a known-present string (`not yet built` → 14 hits in `reference.md`).

**The marker retirement.** `docs/reference.md` § Package layout's `secrets.py` line lost
`— not yet built` **in this commit**. The surrounding paragraph (*"Modules marked `— not yet built`
are specified and unbuilt"*) still describes a **non-empty set of 6**: `docs.py`, `lineage.py`,
`study.py`, `apparatus.py`, `reproduce.py`, `report.py`. The paragraph carries **no count phrase**,
so nothing near the edit needed updating. Comment-column alignment held — the `#` sits at column 40
on 31 of 33 lines including the edited one; the two outliers are a pre-existing continuation line
and the `templates/{...}` branch, neither touched. No trailing whitespace anywhere in the diff.

**The dependency.** `pyproject.toml` declares `python-dotenv>=1.2.3` and `uv.lock` pins 1.2.3 in
both `[package.metadata].requires-dist` and the `[[package]]` entry — they agree. The constraint is
a floor, **not an exact pin**, matching the style of the four existing dependencies. `dotenv` ships
`py.typed` (confirmed in the installed tree), so `mypy` is clean with **no override**, as the brief
predicted. `load_dotenv`'s 1.2.3 signature matches the brief's quotation verbatim.

**No proxy was used for the unpinned claim, and the report says so plainly.** No
`inspect.getsource` or source-text assertion appears anywhere in `tests/test_secrets.py`. The report
states the "never touches provenance" claim has zero mutation coverage at this commit because
nothing calls the module yet, and names task 12 as the owner. That is the honest handling the brief
asked for.

**Housekeeping:** I found `.superpowers/sdd/.gitignore` clobbered to a bare `*` (the known
`sdd-workspace` behaviour) and restored its committed content, per CLAUDE.md. That was pre-existing
and unrelated to this commit.

**On the brief's "75 files" for `ruff format`:** stale, not a defect. The parent commit formats 74
files and this commit adds 2, so 76 is correct and the report's number is right.
