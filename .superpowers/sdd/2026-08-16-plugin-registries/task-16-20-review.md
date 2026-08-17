# H7b Part A — tasks 16–20 review

Reviewed at `deaed2b` against `9479e13`. Gates re-run by me: `uv run pytest` → **2054 passed,
1 skipped, 2 xfailed** (113s); `ruff check`, `ruff format --check`, `mypy` all clean.
Every mutation below was applied by editing the file, run, then reverted by editing back
(`cp` from a pre-mutation copy — never `git checkout --`), `__pycache__` deleted, and
`git status --short src/` confirmed empty afterwards.

---

## The ten verdicts

| Task | Verdict A | Verdict B |
|---|---|---|
| 16 | **PASS** — `check_registration`/`declared_names` are correct and the two message branches are pinned from both sides; mutation (a) (`in declared` → `== declared[0]`) reproduced and FAILs the several-names test while the honouring test stays green | **Minor (M4)** — its § Errors row carries an undated build-state claim ("no task in this slice gives it a caller") that nothing pins; no importable-surface invariant is broken, as neither function is exported |
| 17 | **CRITICAL (C1)** — `plugins.py`'s module docstring still claims "nothing here calls `EntryPoint.load()`", which `load_entry_point` falsifies; the file now holds two sentences that cannot both hold, one of them the argument for the whole mechanism | **Important (I1)** — `discover_local`'s pre-drain was not mirrored, so a stale `_pending` entry is inherited and misattributed (probed); the docstring asserts the opposite. The no-import invariant itself is intact and both positive assertions are unweakened |
| 18 | **PASS on the `Status` row** — probed for real: `uv add` runs, with the constructed requirement, in the project directory, before anything reaches disk (exit 1, `E-UV-ADD`, empty `src/` and `configs/`); all three of task 6's markings are reverted | **Important (I2)** — the ordering guarantee the code comment and test docstring both name (install *before `_claims` resolves*) is pinned by nothing, and the brief's mutation (a) does **not** fail as the report claims; plus M1/M2/M3 |
| 19 | **PASS** — the mutual exclusion fires, is pinned by discriminating mutation (b), and `E-DATA-RESOLVER-UNSUPPORTED` is asserted **alongside** on both arms and never on a total code set, pinned by mutation (c); Part B's retirement stays a one-line deletion | **PASS** — the envelope closure is real: mutation (a) (delete `"data.units.from.glob"`) reddens the control, proving both entries wired; the two false comments were deleted rather than rewritten; the fixture rewrite is behaviour-neutral (`base_config`'s `data` has no `units` key at all) |
| 20 | **PASS on the chain and the filing** — the collision message interpolates only `name` and the joined providers, so it structurally cannot carry a credential; deleting that test was right, and the residual is owned `**Owner: none; accepted**` with "Struck when" naming a sibling entry, not a task | **Important (C2)** — the mutation's silence was read as confirmation; emptying `_claims`' payload leaves all 2054 tests green, and a discriminating test on `partial_templates`/`c.credentials` *was* available and was not written |

---

## Findings

### C1 — Critical (task 17). `plugins.py`'s module docstring is now false, and task 17 made it false.

`src/publishable/plugins.py` lines 1–23 still read:

> "it resolves from **package metadata**: nothing here calls `EntryPoint.load()`, and nothing
> that calls this module may either."

`load_entry_point`, added by this task, is *in that module* and its body is `return ep.load()`.
Its own docstring says "**The one function in this module that imports anything**", so the file
now carries two sentences that cannot both hold — and the false one is the sentence that
justifies the entire entry-point mechanism, in the most-read paragraph of the file.

The task-17 diff hunk on that docstring changed only the `from ... import` lines below it; the
claim was never re-read. This is CLAUDE.md's named habit — *"a sentence can contradict the
argument that justifies the thing it describes"* — and the design spec's own first trap row
(*"Reading a metadata scan as a load"*) is about precisely this guarantee.

**Verified by:** reading `sed -n 1,175p src/publishable/plugins.py` against the diff. No probe
needed. Note the *behaviour* is correct — `scan_group`/`check_registration` genuinely import
nothing, and both no-import assertions
(`test_the_scan_imports_nothing`, `test_get_template_imports_nothing_for_an_installed_claim`)
are untouched by this diff and still pass. It is the claim that is wrong, not the code.

**Fix — re-argue the paragraph, do not patch it with an exception clause.** Appending "except
`load_entry_point`" leaves the *second* clause incoherent: "nothing that calls this module may
either" cannot survive a module that now exposes a loading function, since every caller of
`load_entry_point` calls this module *and* loads. The honest form separates the two things the
paragraph currently conflates — the guarantee (**resolving a name** imports nothing, which is
what `validate` rests on and what `scan_group`/`names`/`check_registration` honour) from the one
function that deliberately leaves it, naming where that function is reached (`run`/`dry-run`,
once a command needs the object) and where it may not be (`validate`). A parenthetical exception
would close this finding while preserving the contradiction in weaker form, which is CLAUDE.md's
"three overreaching claims inside a single commit that was itself fixing overreaching claims".

---

### C2 — Important (task 20), and why not Critical. Emptying `registry._claims`' `partial_templates` payload leaves the whole 2054-test suite green, and a discriminating test was available.

Task 20's chain-check is **correct as far as it goes**: I confirmed by reading `_claims`
(`src/publishable/templates/registry.py`, the `PartialLoadError` raise) that the
`E-TEMPLATE-COLLISION` message interpolates exactly two things — `name` and `who`, the joined
`claim.provider` strings. No declaration reaches it. So the sentinel could never appear, the
brief's step-1 test genuinely could not discriminate, and deleting it was right.

What is wrong is the conclusion drawn from the mutation. I applied
`partial_templates=[...]` → `partial_templates=[]` and ran the **whole** suite: `2054 passed,
1 skipped, 2 xfailed`. The report reads that as "confirming the residual is real and unpinned."
It confirms something stronger and different: the *local* half of the mechanism — that a
collision's payload reaches `Collector.credentials` at all — is now unpinned, and it is
pinnable. `Collector.credentials` is a plain public attribute (`diagnostics.py:28`), set from
`exc.partial_templates` at `validate.py:566–570`.

I built the weaker-but-real test the report says did not exist:

```
$ uv run python /tmp/probe20.py   # templates/mine.py registers "generic", required_env=["SHADOW_KEY"]
code: E-TEMPLATE-COLLISION
partial_templates: [<class '...builtin.generic.GenericTemplate'>, <class '..._mine.Shadower'>]
required_env seen: [[], ['SHADOW_KEY']]
```

An assertion on `partial_templates`' contents (or on `c.credentials` after `validate_config`)
fails under the empty-payload mutant and passes today. This is CLAUDE.md's *"answering a
question with a proxy"* / *"a check that could not fail"* shape: the test that could not
discriminate was correctly deleted, but the one that could was never looked for, and the
mutation's silence was read as evidence of correctness rather than of a gap.

**The residual filing itself is fine.** Owner is `**Owner: none; accepted**` — a disposition,
not a task — and its "Struck when" names the sibling `## OPEN` entry rather than a slice.
Its "Bound on the exposure" paragraph is true, and I verified the claim it rests on above.

**Held at Important rather than Critical**, unlike the slice's three prior Criticals of this
family. Those were tests that named a *live* guarantee and measured something adjacent to it —
the guarantee was reachable and the test claimed to cover it. Here the deleted test was
correctly deleted, the residual filing is accurate, and no behaviour is wrong today: the payload
is built correctly and its one consumer reads it correctly. What is missing is a regression
pin, not a working check. It stays above Minor because the mutation was *run* and its silence
was reported as evidence for a conclusion it does not support.

**Fix:** add the local-claimant test (assert `partial_templates` carries the class, or that
`c.credentials` holds `SHADOW_KEY`) so `_claims`' payload cannot be emptied silently. Do **not**
change the residual entry.

---

### I1 — Important (task 17). `load_entry_point` mirrors `discover_local`'s two arms but not its pre-drain, so it inherits and misattributes a registration it did not make — and its docstring claims otherwise.

`discover_local` calls `drain_pending()` *before* its loop, on every path out, and its docstring
names the exact hazard (`discovery.py`, the paragraph ending *"…rather than left for the next
file's `drain_pending()` to inherit and misattribute"*). `load_entry_point` has no such
pre-drain. Its docstring nonetheless asserts:

> "It is drained rather than kept for the next load either way: **a registration this import
> made is not the next one's to inherit.**"

Probed:

```python
discovery._pending.append(("stale", Stale))       # an earlier module-scope @register_template
load_entry_point(EntryPoint(... "boom_module:resolve" ...))
# → partial_templates = [<class '__main__.Stale'>]
```

A class this import never constructed is carried on this import's refusal. `cli` imports the
experiment package before `validate_config` runs, so a module-scope `@register_template` under
`src/**` is exactly the queued entry `discovery.py` warns about. The success path also never
drains, so a cleanly-loaded `publishable.templates` entry point leaves its registration for
whoever drains next — which is the second direction the quoted sentence claims is covered.

**Impact today is inert** (no production caller, and the failure mode is over-reading a
credential set, which over-redacts rather than under-redacts) — hence Important rather than
Critical. But the brief's whole premise was *"The pattern to copy is the widened one, and
copying the old one drops the payload"*, and half the pattern was copied.

**Fix:** `drain_pending()` at the top of `load_entry_point`, and drain again on the success
return; or narrow the docstring sentence to what the code does.

---

### I2 — Important (task 18). The ordering guarantee both the code comment and the test docstring name — install *before `_claims` resolves* — is pinned by nothing, and the brief's mutation (a) does **not** fail as the report states.

Brief step 8(a): *"Move the `if plugin:` block below `resolve_template`.
`test_a_failed_plugin_install_scaffolds_nothing` must FAIL."* The report says all three
mutations "failed exactly the assertion the brief named."

I applied it literally — moved the block to immediately after `claims = _claims(repo_root)`,
the site that replaced `resolve_template`:

```
uv run pytest tests/test_cli.py -q -k failed_plugin_install  →  1 passed
```

It only fails when the block is moved past the first disk write
(`(pkg_dir / "experiment.py").write_text(...)`), which I confirmed separately (`1 failed`).

So the tests pin *"install before anything reaches disk"* and say nothing about *"install
before the template name is resolved"* — which is the guarantee the code comment gives as the
primary reason (*"the whole point of `--plugin` is that the template it names comes from the
package being installed, so resolving first would refuse a name the install is about to
provide"*) and which
`test_generate_experiment_installs_the_plugin_before_it_scaffolds`'s docstring states outright
(*"The order is the behaviour: `uv add` runs before `resolve_template`"*).

This is the exact shape CLAUDE.md lists — *"a test whose name claims the guarantee"* while the
assertions measure something adjacent. Both fixtures use `--template generic`, a name core
already registers, so no config in the suite makes the two orderings differ.

**Fix:** a test whose `--template` names a template only the (faked) install would provide —
fake `uv_add` to write `templates/<name>.py` — so resolving first would refuse it. Then
correct the report's mutation-(a) claim.

---

### M1 — Minor (task 18). Task 6's marking on the § Creation commands `generate` row was over-reverted: the row no longer mentions `--plugin` at all.

Enumerated by reading `git show 67d7219` (task 6's commit) row by row rather than grepping one
spelling. Task 6 set three markings; all three are gone, but the first went further than
brief step 4 asked:

| Site | Task 6 wrote | Brief step 4 said to remove | Actual |
|---|---|---|---|
| § Creation commands, `generate` row | `` `experiment` accepts `--plugin` (NOT BUILT — the flag parses and is dropped) `` | just the parenthetical | **the whole clause**, incl. the pre-task-6 `` `experiment` accepts `--plugin` `` |
| § Generators, `experiment` row | appended `--plugin`-is-dropped sentence | that sentence | correct |
| § Plugins, opening sentence | `— **NOT BUILT** …` | that clause | correct; step-5 creation-vs-operation paragraph correctly retained |

Not a false claim, and § Plugins documents the flag in full, so the exposure is small. But the
row whose job is to list a command's arguments now omits a built flag while `publishable init`
— documented one row below as *"Alias for `generate experiment`"* — still lists `[--plugin]`.

**Verified by:** reading `git show 67d7219` and `docs/reference.md:3124`.

---

### M2 — Minor (task 18). `uv_add`'s body is executed by no test, and the `@ref` suffix reaching argv (brief step 9's explicit question) is unanswered in the report.

Both CLI tests replace `publishable.generators.experiment.uv_add` wholesale, so the argv
`["uv", "add", requirement]`, `cwd=repo_root`, and the `returncode != 0` → `E-UV-ADD` branch are
covered by nothing that executes. The slow test is an unconditional `pytest.skip` (see the
skipped-test judgment below).

I closed this by probe rather than by test — `uv add` demonstrably runs, in the project
directory, with the constructed requirement:

```
$ publishable generate experiment pilot --template generic \
    --plugin someuser/definitely-not-a-real-repo-xyz ...
  error   E-UV-ADD   `uv add git+https://github.com/someuser/definitely-not-a-real-repo-xyz` failed:
    … Updating https://github.com/someuser/definitely-not-a-real-repo-xyz (HEAD)
    fatal: repository '…' not found
EXIT=1        # and `ls src configs` → both empty
```

That confirms task 18's `Status` row is **true**, and confirms the clean-tree property on the
real path. `plugin_requirement`'s `@ref` handling is still pinned only by the materialize test's
round trip of the *field*; brief step 9 asked the implementer to say whether they added the argv
assertion, and the report does not answer.

---

### M3 — Minor (task 18). `--plugin`'s argument is interpolated raw into the generated YAML.

`materialize.py`: `f"plugin: {plugin if plugin else 'null'}"`. Nothing validates the spec's
shape, and the value is not quoted:

```
$ plugin="{a: b}"  →  line: 'plugin: {a: b}'  →  yaml.safe_load(...)["plugin"] == {'a': 'b'}
```

A generator writing a config whose `plugin` field is a mapping rather than a string. Also
`--plugin null` writes a `null` the field cannot be distinguished from. Edge-case (a
creation-time flag the author types), so Minor, but the field is documented as recording the
argument *verbatim as a note*, and a mapping is not that.

---

### M4 — Minor (tasks 16, 17). Two undated build-state claims now live in a normative § Errors row.

`docs/reference.md:1032–1033`: *"**No task in this slice gives it a caller**, so it is reached
nowhere yet"* and *"the same build state: **no task in this slice gives it a caller either.**"*
Both are true today — I confirmed `check_registration`, `declared_names` and `load_entry_point`
have zero production call sites (`grep -rn` over `src/`), and neither is exported from
`publishable` or listed in § The importable surface, so no shipped-but-unread-export invariant
is broken. But these are perishable build facts stated undated in a document whose device for
exactly this is the `Status` column, and nothing pins them: the day Part B or H7d adds a caller,
both rows read as spec claims a month later. CLAUDE.md's feasibility rule 10 states the
principle; § Errors is not covered by it, which is why this is Minor rather than Important.

---

## Things checked and found sound

- **The no-import invariant (item 4).** `test_the_scan_imports_nothing` (`scan_group`) and
  `test_get_template_imports_nothing_for_an_installed_claim` (`get_template`/`_claims`) are both
  untouched by this diff, and both still pass. Task 17 added exactly one `.load()` call site, in
  the one function whose purpose it is. Neither assertion was weakened. (The docstring problem is
  C1; the *code* is clean.)
- **Task 19's mutual exclusion (item 5).** All three prescribed mutations reproduce:
  (a) deleting `"data.units.from.glob": str` → the closure control FAILs, proving both entries are
  wired; (b) `and` → `or` → FAILs on the `glob`-alone control; (c) guarding the resolver emit with
  `and "glob" not in source` → FAILs on `assert "E-DATA-RESOLVER-UNSUPPORTED" in found`. The
  alongside-never-instead-of discipline (decision 7) is pinned by (c), asserted alongside on both
  the both-keys and resolver-only arms, and never on a total code set. Part B's retirement stays a
  one-line deletion.
- **The fixture rewrite (item 6).** True and behaviour-neutral. `base_config`'s `data` block
  (`tests/test_validate.py:31–35`) holds `input_dir`, `output_dir`, `input_manifest_policy` and
  **no `units` key at all**, so `write_config`'s walker (`node = node[h]`) raises `KeyError` on
  `"data.units.from"`. Overriding `"data.units"` as a whole mapping adds a block that did not
  exist, so no sibling key is dropped and no finding is suppressed.
- **Task 16's tests.** Mutation (a) (`in declared` → `== declared[0]`) FAILs
  `test_an_object_registered_under_several_names_satisfies_any_of_them` and leaves the honouring
  test green, exactly as the brief predicted — membership is distinguished from equality by a
  two-key fixture, and the two message branches are pinned from both sides.
- **Task 17's `SystemExit` arm.** Deleting it FAILs
  `test_a_plugin_module_calling_sys_exit_is_contained_too`. One correction to the brief and report:
  it fails as an ordinary reported failure (pytest intercepts `SystemExit` raised inside a test
  body), not by pytest itself exiting. The observable the brief named does not occur; the
  discrimination does.
- **Task 18 mutations (b) and (c).** Both reproduce, and (c) confirms the brief's warning — the
  materialize test does *not* catch writing the field from the requirement; the CLI test does.
- **No double-report from task 19's new call.** `_check_units_source` calls `_units_declaration`,
  which `validate_config` and `_check_units` also call — but that helper suppresses a duplicate
  `E-CONFIG-SHAPE`/`data.units` already in `c.findings`, so the extra call adds no finding.
- **Item 7 — Part B's options are not narrowed.** `cli.command_run`'s credential computation and
  `_check_units`' `except ContractError` guard are untouched (`cli.py` diff is one line;
  `validate.py` adds one function and one call). `_check_units_source` is a `c.error(...)`, runs
  *before* `_check_units`, and wraps nothing — the credential-move fix and the widened-guard fix
  both stay open.
- **Task 19's document rows.** `E-UNITS-SOURCE-AMBIGUOUS`'s § Errors row and § Validation row are
  placed beside the siblings the brief named by function, both anchors (`#where-units-come-from`,
  `#plugins-where-domain-knowledge-lives`) resolve, and the two false comments in `envelope.py`
  were **deleted** rather than rewritten, as instructed.

---

## Judgment on the skipped test

`tests/test_cli.py::test_uv_add_really_installs` is **not a test that skips by default — its
body is an unconditional `pytest.skip(...)`, so it never runs under any invocation**, including
`-m slow` or `--runslow`. It is a test that does not exist, wearing a marker. That is worse than
the prompt's framing, and worth stating plainly in the ledger: the `slow` marker now has exactly
one user and that user is a no-op, so `-m slow` is currently a way to run nothing.

**But it is not the sole pin for task 18's headline behaviour, and `--plugin` is genuinely
recognised rather than swallowed.** Both CLI tests drive `main` end to end and run unskipped:
`assert calls == [(str(root), "git+https://github.com/someuser/publishable-llm")]` fires only if
`_dispatch_generate` actually threaded `plugin=opts.get("plugin")` through, which is exactly the
gap the task-6 reviewer flagged when `_dispatch_generate` swallowed every unknown `--key value`
identically. Mutation (b) (`if plugin:` → `if True:`) FAILs on that test's control, so the flag's
recognition, its optionality, the field write, and the clean-tree-on-failure property are all
pinned by executing tests. I additionally closed the question by real probe (M2): `uv add` runs,
with the constructed requirement, in the project directory, before anything reaches disk.

What the skip leaves genuinely unpinned is narrower than "task 18's headline": it is `uv_add`'s
**body** — the argv, the `cwd`, the returncode branch — since both tests replace the function.
Brief step 6 explicitly sanctioned writing it as a `pytest.skip` if no offline-installable
`git+https://` dependency existed, and none does (I confirmed a scaffolded project cannot even
resolve `uv add`, since it depends on the unpublished `publishable` itself). So this is
**Minor-with-a-residual, not a blocker** — but neither brief step 9 nor the report says "no test
executes `uv_add`'s body", and that sentence belongs in the ledger rather than being left for the
next reader to rediscover.

**Recommendation:** keep the skip, but (a) state the residual in the report and the ledger, and
(b) prefer `pytest.mark.skip(reason=...)` at decoration over a marked-then-skipped body, so the
suite reports it as `skipped` for a stated reason rather than as a `slow` test that silently
opts out of its own marker.

---

## Housekeeping

`.superpowers/sdd/.gitignore` is clobbered to a bare `*` in the working tree (present before this
review began — `scripts/sdd-workspace` via `task-brief`). Restore its content before committing
these records, and use `git add -f`.
