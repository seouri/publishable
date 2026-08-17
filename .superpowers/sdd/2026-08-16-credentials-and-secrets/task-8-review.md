# Task 8 review: the two load sites, and the reconciled single-site sentence

**Reviewed:** `4c79417..4d1dc18` (`99a62c3` feat, `4d1dc18` report) on `h7c-credentials`.

**Verdicts — spec compliance ✅, task quality ❌.** Decision 5 is built exactly as specified: two
sites, in two modules, each separately pinned; no `command_draft` stub; the single-site sentence
reconciled; `validate`'s promise untouched. Quality fails on two Important defects in a **normative**
document, both of which are findable by reading the section the prose cites — the class this slice
has already produced 9 of its 12 findings in, and the one the brief named explicitly.

## What I verified myself, not from the report

- **Full suite:** `uv run pytest` → **1973 passed, 2 xfailed**. `ruff check .` clean;
  `ruff format --check .` → 76 already formatted; `mypy` → clean, 43 source files.
- **Patch target (check 1).** `src/publishable/cli.py:59` and `src/publishable/validate.py:24` each
  do `from publishable.secrets import load_env`, binding **two separate module attributes**.
  `grep -n load_env` over `src/` and `tests/` shows exactly those two imports and exactly two call
  sites (`cli.py:1281`, `validate.py:516`). So patching `publishable.validate.load_env` in the `cli`
  test cannot reach `cli`'s call — **the target is correct**, and it is the only target that makes
  the test discriminating. The `validate` test patches nothing but `delenv`, which is right: it is
  the unpatched behaviour of its own site.
- **Both sites separately pinned (check 2).** Ran both mutations, each by editing the call to
  `_ = load_env` (kept a copy in scratchpad, reverted by editing back, `diff` against the copy →
  identical, `__pycache__` cleared between runs, full suite re-run green afterwards):
  - `validate_config`'s call removed → `test_validate_loads_dot_env_from_the_repository_root`
    **FAILS** (`assert None == 'from-the-file'`); the `cli` test **passes**.
  - `command_run`'s call removed → `test_run_loads_dot_env_itself_rather_than_relying_on_validate`
    **FAILS**; the `validate` test **passes**.
  Neither mutation reddens both, neither reddens neither. The two sites are pinned independently, as
  claimed.
- **`validate`'s promise (check 3).** The promise text occurs **exactly once** in the repo, at
  `docs/reference.md:3117`, and the diff does not touch it — the promise was **not** weakened. It is
  a row of the § CLI reference table (see Important 2 for where that lands the citation).
- **`draft`/`resume` (check 4).** No `command_draft` or `command_resume` exists anywhere in `src/`.
  `cli.NOT_BUILT_COMMANDS` (read at `cli.py:121-135`) contains `draft`, `resume` **and** `dry-run` —
  all three the new sentence names. "In this build the executing site is `run`; … inherit it when
  each is built" reads as specification plus a dated-by-phrasing build note, and `in this build` is
  heavily precedented in `reference.md` (13+ instances, alongside the § CLI reference `Status`
  column). **No finding.**
- **Environment hygiene (check 6).** `tests/conftest.py`'s autouse `_restore_environ` is untouched
  and **no second fixture was added** — the diff contains no `conftest.py` change. The `validate`
  test's negative arm (`.env` unlinked → name unset) is not a bare absence: it sits after a positive
  arm that must report `"from-the-file"`, and both arms `monkeypatch.delenv` first, so it fails on a
  build that never loads instead of passing on a machine that happened to export the name. The `cli`
  test's assertion is positive by construction (`"token_len": 8` must appear).
- **Sweep (mechanical pass).** Grepped `dotenv`, `\.env`, `before any step runs` over `README.md`,
  `docs/design-principles.md`, `docs/experimental-designs.md`, `CLAUDE.md` **and**
  `docs/feasibility-llm-growth-studies.md` — no other statement of where `.env` is loaded, so the
  replaced sentence had no siblings. Proved the sweep can fail by grepping `credential` over the same
  file list (4 hits in the feasibility analysis). `#validation` (line 214) and `#cli-reference`
  (line 3093) both resolve; the edited line carries no trailing whitespace, tab, or invisible unicode.

## Findings

### Important 1 — "three of its checks ask whether a variable is *set*" is **two**, and the third is already built proving it

`docs/reference.md:3472` (and the same claim in `src/publishable/cli.py:1277`'s comment: "three
§ Validation rows ask whether a variable is set").

§ Validation carries three credential rows: *Credentials present* (`E-CRED-MISSING`), *Credentials a
swept value needs* (`E-CRED-PARAM-MISSING`), and *`requires_env` covers its choices*. Only the first
two ask whether a variable is set. The third is a **totality** check on the declaration — decision 2
rules it `E-TEMPLATE-LOAD` from `Param.__init__` — and it **ships today**, pinned by
`tests/test_validate.py::test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding`,
which passes with no environment read at all. So the count is not merely arguable; the repo already
contains the counterexample. `grep -n "os.environ\|missing_env\|credential_values\|getenv"` over
`validate.py`, `cli.py`, `runner.py`, `templates/registry.py` returns **nothing**, confirming no third
environment-reading check exists or is planned outside the two `E-CRED-*` codes.

This is a normative document justifying the whole two-site design with a false count, and
`CLAUDE.md` names count phrases as a repeat offender. **Suggested repair: drop the count rather than
change 3→2** — "loads it because its credential checks ask whether a variable is *set*" is
self-maintaining where a number is a maintenance obligation. Fix the `cli.py` comment in the same
edit. **Do not retro-edit the design doc's decision 5**, which is where the "three" originates — the
development record is corrected by appending, never rewritten.

### Important 2 — the promise is cited to the wrong section, at three sites, and one of them is a link a reader will follow

`docs/reference.md:3472` writes **`[validate's promise](#validation)`**. The promise —
*"creates nothing and reaches nothing off the machine"* — is not in § Validation. It occurs exactly
once in the repo, at `docs/reference.md:3117`, a row of the § CLI reference table under
**### Operation commands**. Verified two ways: a `sed`-range grep of the whole § Validation section
for the phrase returns empty, and an `awk` walk of headings up to 3117 lands on
`### Operation commands`. A reader following `#validation` for the promise finds nothing there.

The same misattribution appears in `src/publishable/validate.py:512` ("`reference.md` § Validation
promises `validate` …") and in the new test's docstring at `tests/test_validate.py:12294`. Note the
sentence contains **two** links to `#validation`: the earlier `[validate](#validation)` is correct
and should stay; only the promise link is wrong. It should point at `#operation-commands` (or
`#cli-reference`).

### Minor 3 — `_local_template` is added with zero callers, and its comment describes an empty set

`tests/test_cli.py:53,155,180-187`. Brief-authorized (task 12 step 7 is the intended caller), and
adding it with `_env_file` in one signature edit is reasonable. But **deleting its two-line body
leaves the whole suite green** — it is unexercised code today, and its inline comment asserts "the
one name every caller that passes this registers" about a set with no members. Not a defect to fix
now; flagged so **task 12 must actually exercise it**, or it should be removed rather than left as
dead scaffolding with a comment that reads as a verified convention.

### Minor 4 — the `_env_file` comment's causal chain is inoperative

`tests/test_cli.py:177-179` and the matching docstring paragraph: "the scaffold's own `.gitignore`
opens with `.env`, so this never reaches the commit below and never makes `src/**`+`templates/**`
dirty." The gitignore claim is true (`scaffold.py:8-10` — a comment line then `.env`). But `.env` is
written at the **project root**, and `code_hash` covers `src/**` and `templates/**` only, so it could
not dirty those trees whether or not `.gitignore` named it. The reason offered is not the reason it
works. Reword, or drop the second clause.

## The named position gap (check 5) — a **note**, not an Important finding, with a precision task 9 needs

Nothing pins the position of the `validate`-site call, as the report says: a mutant moving it past
`resolve_template`, or to the end of `validate_config`, passes
`test_validate_loads_dot_env_from_the_repository_root`, which asserts `os.environ` only after
`validate_config` has returned.

**Does anything downstream depend on the load preceding `resolve_template` today? No.**
`grep -n "os.environ\|missing_env\|credential_values\|getenv"` over `validate.py`, `cli.py`,
`runner.py` and `templates/registry.py` returns nothing — core reads no environment variable at all
at this commit. The only thing between the load and the end of `validate_config` that could read the
environment is **user** code executed by a project-local template's import, which core does not
promise anything about. So this is a note.

**But task 9's owner needs one correction before inheriting it.** Task 9's `required_env` check reads
the **resolved** template, so it necessarily runs *after* `resolve_template` — which means a mutant
moving the load to just after `resolve_template` will pass task 9's test too. What task 9 can pin is
"loaded before the first check that reads the environment," which is strictly **weaker** than the
position the brief's comment claims ("before any check that asks whether a variable is set" is
satisfied by both placements). Task 9 should either pin that weaker, real property and reword the
comment to match it, or state that the stronger position is unpinned by design. Left as-is, task 9
files this same gap straight back.

## What the two mutations do not reach (the check-that-could-not-fail pass)

Per test, the single-line mutation that reddens it:

- `test_validate_loads_dot_env_from_the_repository_root` — delete/no-op `load_env(repo_root)` in
  `validate_config` (**run, confirmed red**). Also reddened by `load_env(None)`, since the test's
  `.env` sits at the `git_repo` root, so the argument is pinned too.
- `test_run_loads_dot_env_itself_rather_than_relying_on_validate` — delete/no-op `load_env(repo_root)`
  in `command_run` (**run, confirmed red**). Also reddened by moving that call after `execute_plan`,
  so this test pins the `cli` site's **position** as well as its existence — the property the
  `validate` site lacks.

Neither reaches: (a) the `override=False` behaviour through either wired site — accepted, pinned in
`tests/test_secrets.py`; (b) the `validate` site's position, above; (c) `_local_template`, which no
test exercises at all (Minor 3).
