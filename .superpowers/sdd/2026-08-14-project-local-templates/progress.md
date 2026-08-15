# SDD ledger — plan: docs/superpowers/plans/2026-08-14-project-local-templates.md

Branch h7a-local-templates, forked from main at 4681bda.
Spec: docs/superpowers/specs/2026-08-14-project-local-templates-design.md (read; it is the binding
authority and the plan argues from it).
Measurement: docs/superpowers/H7a-SCOPING.md

## Pre-flight scan

Files each task touches, then every pair sharing one.

| Task | Files |
|---|---|
| 1 | discovery.py (create), __init__.py, test_templates.py |
| 2 | discovery.py, test_templates.py |
| 3 | registry.py, test_templates.py, test_materialize.py, test_validate.py |
| 4 | validate.py, test_validate.py |
| 5 | cli.py, generators/experiment.py, test_cli.py |
| 6 | discovery.py, test_templates.py |
| 7 | discovery.py, reference.md, test_templates.py |
| 8 | discovery.py, reference.md, test_templates.py |
| 9 | cli.py, generators/*, test_cli.py |
| 10 | materialize.py, validate.py, reference.md, test_materialize.py, test_validate.py |
| 11 | reference.md, cli.py |
| 12–15 | reference.md (+ validate.py, test_validate.py at 14) |

| Pair | Shared | Produces vs consumes | Found |
|---|---|---|---|
| 1 → 2 | discovery.py | 1 makes `register_template`/`drain_pending`; 2 makes `discover_local` draining them | consistent |
| 2 → 3 | — | 2 makes `discover_local(repo_root)`; 3 calls it per call | consistent |
| 3 → 4,5 | registry sig | 3 adds the optional repo root; 4 and 5 pass one | consistent |
| 1,2,6,7,8 | discovery.py | sequential edits to one new file | no conflict; 6 constrains 1's storage choice, and task 1 says so |
| 4,10,14 | validate.py | 4 hoists; 10 touches `_check_versions`; 14 the E-TEMPLATE-UNKNOWN message | three different functions |
| 5,9,11 | cli.py | 5 wires a call site; 9 routes a generator; 11 edits a constant | **CONFLICT — see ruling 1** |
| 7,8 | reference.md registry table | two insertions into one sorted table | ordered; each must re-check rows its own insertion moved, including the row the other added |
| 7,8,9,10,12,13,14,15 | reference.md | eight sequential edits | no textual overlap; the standing rows-moved rule covers it |

| Task | Self-consistency | Found |
|---|---|---|
| 1 | creates discovery.py; task 13 later documents it | see ruling 2 |
| 9 | its tests need `generate template` to route | **blocked by the constant — ruling 1** |
| 13 | conditional on "if task 2 lands a new file" | **task 1 creates it, not task 2 — ruling 2** |
| others | tests specified match code specified | consistent |

**Ruling 1 — merge task 11 into task 9; the plan is 14 tasks, not 15.** `_dispatch_generate` checks
`if kind in NOT_BUILT_GENERATORS` *after* the `experiment`/`step` branches, and the CLI-table tests
invoke every marked generator and assert it prints the unbuilt diagnostic. So task 9 implementing
`generate template` while task 11 still holds it in the constant leaves the suite RED between the two
commits — and the plan's own task 11 says the three edits "must land atomically or the suite fails".
It named the wrong three: the *implementation* is the fourth. Cost if wrong: one extra commit's worth
of churn, and task 9's diff is larger to review.

**Ruling 2 — task 13 is unconditional.** Its text conditions on "if task 2 lands a new file", but task 1
creates `discovery.py`. The condition is satisfied by task 1. Cost if wrong: a line in § Package layout
describing a module that exists, which is what the section is for.

Task 1: complete (commits 4681bda..227936d, review clean). register_template + drain_pending in templates/discovery.py, exported from publishable. Reviewer re-ran both mutations independently and confirmed the identity assertion pins the class rather than its name — a same-named wrapper would fail too.
Task 2: complete (commits 227936d..1621e7c, review clean). Eager discover_local(repo_root). Reviewer
  re-ran the eager mutation (import only the named file → the eager test dies) and confirmed discovery
  takes no name argument at all.
Task 2 → carried into TASK 6's dispatch, sharpened by the reviewer: the `module_name = path.stem`
  footgun is NOT a concurrency issue as the report framed it. Reproduced single-threaded: a
  `templates/json.py` whose own top level does `import json` gets ITSELF back recursively — because
  `sys.path.insert(0, templates_dir)` plus purging `sys.modules["json"]` makes any nested import from
  that file resolve to the local file, deterministically, every call. `publishable` itself imports `io`,
  so `templates/io.py` risks the same during its own import. Task 6 must carry this repro, not the
  milder concurrency framing.
Task 3: commit 80fe227, fix round 1 in flight. Spec ✅. get_template/template_names take an optional
  repo root and merge per call.
Task 3: MY BRIEF'S PREMISE WAS WRONG, and the implementer proved it with --collect-only before editing.
  I claimed six call sites "break" on the signature change; every existing call passes ONE positional
  argument, so a defaulted second parameter breaks none. It edited only registry.py and
  test_templates.py. Upheld.
Task 3: A COULD-NOT-FAIL CHECK, found by the reviewer. Mutating the merge so every local name resolves
  to CORE's GenericTemplate leaves ALL 16 tests in test_templates.py passing — "a local template
  resolves by name" was proved about the NAME only, never about the template. Fixed with an identity
  assertion rather than left to task 6's __doc__ checks.
Task 3: the implementer's own justification for an added test was false — it claimed none of the brief's
  three examples could distinguish per-call merge from merge-once-cache-forever, but
  test_template_names_includes_locals_and_stays_sorted calls template_names(root) then template_names()
  in ONE test and dies to an unkeyed cache by itself. Test kept, reason corrected.
Ruling: "core wins over a same-named local" is a DEFENSIBLE INTERIM BEHAVIOUR but its docstring asserted
  it as designed policy, borrowing "resolved by name, never by load order" — the phrase § Creating a
  plugin uses as its reason for REFUSING the shadow — to justify silently resolving it. Behaviour stands
  (no local file can change what a config means); docstring marked interim and names task 7. Cost if
  wrong: task 7 refuses the case anyway, so the interim is unobservable after it lands.
ROUTED to task 4: tests/test_validate.py's one-argument monkeypatch `lambda name: RuleBreaker()` breaks
  the moment validate calls get_template(name, repo_root) — that call sits OUTSIDE any try, so it raises
  TypeError out of validate_config. Loud, not vacuous. Task 4 changes it to `lambda name, repo_root=None`.
ROUTED to task 7: it needs registry.py in its file list. Importing _BUILTIN into discovery.py is a
  CIRCULAR IMPORT in both directions (registry imports discovery at module level), verified by mutation
  — so the local-shadows-generic check cannot live in discovery.py with a module-level import. And
  discover_local's `found[name] = cls` silently drops the first provider on a local × local collision,
  while task 7 promises both provider paths in the message: the return shape must carry the claiming
  path per name. The pre-flight table did not list task 7 as touching registry.py; it does.
Task 3: complete (commits 1621e7c..9e23e9e, review clean). Identity assertion added; docstring marked interim; the false coverage claim retracted.
Task 4: commit 15ee377, fix round 1 in flight. Spec ✅. find_repo_root hoisted above the template check,
  silent on failure; the documented early-return order preserved (E-TEMPLATE-UNKNOWN still fires exactly
  once, asserted as an exact finding set rather than membership — a membership assertion cannot see an
  ADDED finding, which is precisely what would break the order). The routed monkeypatch was widened to
  `lambda name, repo_root=None` in the same commit, and the test it belongs to still asserts its code.
Task 4: ANOTHER CHECK THAT CANNOT FAIL, and the implementer flagged the shape while getting the reason
  wrong. Its new no-repo test is a BYTE-FOR-BYTE duplicate of the pre-existing
  test_the_genuine_no_repo_case_returns_quietly; the report claimed they "guard different call sites",
  but both patch the module-level `validate_mod.find_repo_root`, which every call site reads from the
  same namespace — so patching it patches the hoisted call AND _check_data's at once. Proven by
  mutation: propagating the ContractError, and reporting a finding on a missing repo, each killed BOTH
  tests identically. No mutation distinguishes them, so the new test adds zero coverage.
  Fix: delete the duplicate and extend the surviving test's docstring to record that it now also covers
  the hoisted call — or isolate the hoist at a narrower seam if that costs a couple of lines.
Task 4: complete (commits 9e23e9e..b75a485, review clean). The implementer took the better of the two
  offered routes — narrowed the test's seam so it isolates the HOISTED find_repo_root call rather than
  deleting the duplicate — and proved the two tests now exercise different call sites with an ASYMMETRIC
  mutation: one inside _check_data's own except-branch that the pre-existing test catches and the
  narrowed hoist test correctly does NOT. That asymmetry is the proof a duplicate could never produce.
  Report retracts the earlier defence-in-depth framing.
Task 5: commit e5d727b, fix round 1 in flight. Spec ✅. cli.command_run's aggregate block and
  generate_experiment now pass a repo root. Reviewer confirmed by mutation that the two sites are
  SEPARATELY sensed (nulling each in turn fails only its own tests), that the --template nope control
  catches a stop-checking implementation (patched get_template to fall back to GenericTemplate on any
  unknown name; both controls failed loudly), and that there is no hidden fourth aggregate path — draft,
  resume and dry-run all route through the single command_run.
Task 5: the implementer's own advisor pass caught two issues before commit — a fixture importing from
  publishable.templates.builtin rather than the one import root, and a weak identity assertion. Both
  fixed pre-commit; the reviewer verified the import-root fix and found ONE identity assertion still a
  proxy: `doc["parameters"] is None` proves "not generic", so any empty-parameter_spec template passes
  equally. Same shape as task 3's merge mutation that left all 16 tests in a file passing. Fix round
  gives MyAssay a distinctive non-empty spec so the config carries a fingerprint.
Task 5: complete (commits b75a485..33e4ce1, review clean). MyAssay now carries a distinctive parameter_spec fingerprint asserted exactly; the CLI control asserts E-TEMPLATE-UNKNOWN rather than only EXIT_WRONG. Both mutation-proved.
Task 6: commits 565d9af, 3beabee; fix round 1 in flight on a CRITICAL. Spec ✅, strong process.
Task 6: MY BRIEF'S PREMISE FOR FAILURE 1 WAS WRONG and the implementer refused to manufacture a failure
  to match it. Verified at 33e4ce1: plain two-repo PASSES (the old code popped the stem before and after
  each import), sibling .py helper PASSES, helper PACKAGE fails, templates/json.py fails. The leak shape
  is a helper DIRECTORY — regular or namespace package — which discovery never imports directly and so
  never popped. The implementer's own summary sentence said "sibling-helper shape", contradicting its own
  table and fixture; my brief inherited that error.
Task 6: the implementer caught an incomplete rule in its own second pass — scoping the sys.modules
  restore by __file__ misses NAMESPACE PACKAGES (templates/plain/ with no __init__.py has no __file__),
  leaving A's package cached for B. _is_local now tests __file__ OR any __path__ entry.
Task 6 CRITICAL: `del sys.path[entry]` uses an index captured BEFORE exec_module, so a template that
  mutates sys.path reopens the exact cross-repo leak this task closes. Measured: repo A's templates/ left
  on sys.path permanently, a legitimate pre-existing entry silently DELETED instead, and repo B served
  repo A's helper (origin A, A). Trigger is any sys.path mutation during import, including by a library
  the template imports. The comment asserts a correctness property the code lacks. ALL 19 TESTS PASS WITH
  THE BUG — the sixth could-not-fail of this slice. Fix is a snapshot/restore symmetric with the
  sys.modules one; a reverse string scan is NOT sufficient, because a template appending its own dirname
  makes the scan delete the template's copy and leave discovery's.
Ruling: widen TASK 15 by one sentence to own the sys.path.append precedence — templates/ goes on the END
  of sys.path, so a real installed `x` beats templates/x.py. No task in 11-15 owned it (13 only adds
  discovery.py to § Package layout; 15's three steps are the eager-import sentence, the README gap and
  __pycache__), and this slice's task 15 explicitly forbids spec-defects.md as gitignored. Cost if wrong:
  one sentence in the wrong section, moved later.
ROUTED to task 7, stronger than the implementer stated: the restore DELETES the module object, so
  inspect.getfile raises TypeError — the file path is UNRECOVERABLE from the class. Path-threading for
  "naming both providers" is mandatory, not stylistic. Return shape otherwise unchanged.
Task 6: complete (commits 33e4ce1..afd1bb1, review clean). 1657 passed + 2 xfailed.
  Critical closed and controller-verified independently: two repos each with a sys.path-mutating
  template now give A->A, B->B with sys.path restored whole. The implementer strengthened the test past
  what was asked — each template does BOTH sys.path.insert(0,'/zzz') AND append(dirname(__file__)), so
  the `remove`-based variant dies too (remove takes discovery's occurrence and leaves the template's).
  Three of the five mutations now kill on the cross-repo leak ITSELF rather than on a __module__
  inequality — a strictly stronger kill than the first round had.
  Residue assertion no longer enumerates names: _modules_under() computes every sys.modules key whose
  __file__ or __path__ resolves under the directory, so a stale plain.data with plain evicted is caught.
Task 7: commit 9942c28, fix round 1 in flight. Spec ✅, quality strong. E-TEMPLATE-COLLISION minted.
  Local × local refused in discover_local (the only place holding a claiming file's path and, being
  eager, every claim; scanned in NAME order so import order decides nothing — probe-verified with the
  later-sorting collision's files importing first). Local-shadows-generic refused in registry._merged,
  because registry imports discovery so core's names cannot travel the other way.
  Interface change FORCED and verified: discover_local -> dict[str, LocalTemplate] (NamedTuple of cls +
  provider), because task 6's sys.modules restore deletes the module object — inspect.getfile raises
  "is a built-in class" and cls.__module__ is not in sys.modules. The path is unrecoverable.
  The reviewer ran a mutation the implementer did not — firing the shadow check on EVERY local template —
  and found 12 pre-existing tests catch it, so the brief's control not reaching _merged costs nothing.
  Task 3's interim docstring is retired.
Task 7 Important: A COUNT PHRASE WENT STALE FOUR LINES BELOW THE COUNT THE REPORT SAYS IT CHECKED.
  reference.md said E-CONFIG-TYPE/E-CONFIG-KEY-UNKNOWN are found "before either of the later two returns
  is possible"; check_envelope runs inside _check_shape, so after the collision return there are THREE.
  Correct under the old three-fault text, stale after the insertion. The standing rule holds: an
  insertion invalidates counts NEAR it, not only the one it obviously touches.
Ruling: ADD the § Errors core raises row. The implementer's reconcile rested on that table being scoped
  to "the run-time surface, where there is a step to raise into" — but six E-RUN-*/E-REPL-ORDER rows have
  no step either (the table's own closing prose concedes it), E-STEP-NAME-COLLISION is raised as an
  experiment loads, and the convention for a DUAL-SURFACE code is both tables:
  E-DATA-CLUSTER-UNKNOWN, E-UNITS-COLLAPSE-RULE, E-DATA-WEIGHT-INVALID, E-DATA-MEASUREMENTS-* all appear
  twice. E-TEMPLATE-COLLISION is dual-surface — every get_template caller passes a root and main prints
  exc.code, so run and generate meet the raise. Cost if wrong: one row in a table that documents it.
Task 7: complete (commits afd1bb1..f8dd07c, review clean). 1663 passed + 2 xfailed.
  The implementer conceded the process failure precisely: "I grepped for the phrase I had edited rather
  than reading the paragraph the insertion lands in." Re-reading as prose, it then found THREE MORE
  claims the § Errors core raises insertion falsified that neither the controller nor the reviewer had
  named — the "unlike every row above, none of the six" clause, the "covers exactly the run-time surface"
  close, and the same claim mirrored in § Errors `validate` reports' intro. It also caught its own first
  draft using the banned positional construction ("beside E-STEP-NAME-COLLISION above") and removed it.
  Stacked decorators now dedupe providers and carry a DIFFERENT remedy — "A, twice by the same class …
  Remove one" versus "A and B … Rename one" — because deleting a line is what fixes it. The suffix's
  justification was narrowed to "two classes in one file" rather than claiming coverage it lacked.
Task 8: commit e264f11, fix round 1 in flight. Spec ✅. E-TEMPLATE-LOAD minted for three shapes —
  raises on import, registers nothing, registers a non-BaseTemplate — each verified a FINDING rather than
  a raise at both discover_local and validate_config.
MY PRE-FLIGHT SCAN MISSED A CROSS-TASK CONFLICT, and the implementer caught it before writing code:
  task 6's helperx.py fixture LEGITIMATELY REGISTERS NOTHING (the sibling-helper convention, reviewed and
  mutation-tested), which directly contradicts task 8's "registers nothing → E-TEMPLATE-LOAD". My scan
  table paired tasks by FILE, and these two collide by BEHAVIOUR — task 8's new rule invalidates task 6's
  fixture without either touching the other's code. Resolution accepted: reuse discover_local's existing
  __-prefix skip, rename to __helperx.py, and document the convention normatively, since it changes what
  a well-formed templates/ may contain. The reviewer verified by mutation that task 6's tests still test
  what they claimed under the rename.
Task 8: three Importants in the fix round. (a) A template calling sys.exit() STILL ESCAPES AS A
  TRACEBACK — except Exception does not catch SystemExit, and validate.py's own entrypoint handler
  catches it explicitly eight lines away, calling it "the one outcome validate is contracted never to
  produce". (b) A validate.py comment now says "one today, E-TEMPLATE-COLLISION" when there are two —
  in a file the diff never touched. (c) A self-contradicting clause introduced in the very paragraph the
  implementer edited, listing a load failure among what CAN appear beside a collision while its own
  parenthetical says it never can.
Task 8: seventh vacuous assertion of the slice — `"impostor" in str(excinfo.value)` is satisfied by the
  interpolated PATH alone, so the registered name and offending class are untested. And a test docstring
  claimed an attribution the reviewer disproved by mutation: the assertions it credits do NOT catch a
  diagnostic built inside _import_file; a different test does.
Task 8: complete (commits f8dd07c..c0da6a7, review clean). 1671 passed + 2 xfailed. SystemExit now caught ahead of except Exception, mirroring validate_config's entrypoint precedent — controller-verified: a template doing sys.exit(3) yields ContractError E-TEMPLATE-LOAD. Both optional items taken.
Ruling (task 9 review, Minors): two Minors closed inside task 9 rather than deferred to the final
  whole-branch review, against the skill's "Minor findings never enter the loop" rule. Grounds: both are
  FALSE SIGNALS IN A NORMATIVE DOCUMENT, not polish. Marking the `template` row NOT BUILT while its
  immediate neighbour carried the identical unbuilt claim made the `experiment` row read AFFIRMATIVELY
  TRUE — the marking created a defect that did not exist before it. That is this slice's own standing
  class ("a comment claiming a guarantee the branch does not provide"), and shipping one knowingly for
  six tasks is worse than one clause now. The `__`-prefix prose likewise stated a rule the code ANDs as
  two. Cost if wrong: two clauses of churn in a table task 15 reopens anyway.
Ruling: task 15's brief RE-ANCHORED in the plan before dispatch, per the task 9 reviewer's handoff. Its
  step 2 quoted § Generators promising the parameter table "is added to the README" — a phrase task 9
  DELETED. An executor would have grepped for it, found nothing, and either invented a region (the exact
  act decision 4 forbids) or reported the task vacuous. Step 2 now says the `template` half is already
  marked and scopes the task to the gap itself. Added 2b (the `experiment` row's twin claim, plus
  `required_env` as a second specified reader of a dead member — § The generated README) and 2c
  (generalize § Exit codes' single-member `E-STEP-EXISTS` clause to the family, now four members, rather
  than minting a fourth row). Cost if wrong: task 15 grows from 4 steps to 6 in one document.
Task 9: complete (commit 92a34d3 — AMENDED, sha moved from 70b70d0; task 10's BASE is 92a34d3, not
  70b70d0). 1676 passed + 2 xfailed, ruff/mypy clean. Spec ✅, quality high — the reviewer called it the
  strongest process discipline of the slice, and all four of the implementer's raised points were upheld.
  Task 11 ABSORBED here by earlier ruling.
  MY STRENGTHENING SUGGESTION WAS PARTLY WRONG AND THE IMPLEMENTER CORRECTED IT. I proposed replacing the
  dead-members substring check with an `ast` parse of the class body. An ast parse CANNOT SEE A
  COMMENTED-OUT MEMBER — comments are not in the tree — so the swap would have LOST the case the
  substring check exists for. The two checks catch OPPOSITE failures: substring catches a member emitted
  commented out; the parse catches a mention that is not a declaration. It kept both, and proved each by
  a mutation the other survives (`# apparatus_probe = None` kills only the text loop; renaming
  `parameter_spec` to `parameter_spec_typo` kills only the set equality). Generalizes: WHEN A REVIEWER
  PROPOSES A STRONGER CHECK, ASK WHETHER IT IS STRICTLY STRONGER OR MERELY DIFFERENT — two dimensions is
  often the answer, and "replace X with Y" quietly drops a dimension.
  Both required clauses landed. The implementer caught its OWN first draft using a positional table-row
  phrase ("for `template` below") and rewrote it to name the command — that class has now been wrong
  twice in this repo, and this is the second consecutive task where the implementer caught it unprompted.
Task 10: dispatched (sonnet). BASE 92a34d3.
Ruling (pre-dispatch, task 10): THE BRIEF'S SECOND TEST COULD NOT FAIL, caught by reading
  _check_versions before dispatching rather than at review. Its guard opens `if not declared or declared
  == TEMPLATE_VERSION: return` — so once materialize stops writing a version for a local template, "no
  W-TEMPLATE-VERSION for a local config" is ALREADY TRUE via a falsy branch that predates the slice. The
  plan's own step 5 mutation ("suppress the warning for every template") would still have failed the
  generic control, so the mutation discipline would NOT have caught this one. Instructed: the config
  under test must DECLARE a template_version DIFFERING from core's, under a local template, and assert no
  warning — the only shape where suppression does work, and the correct behaviour besides, since decision
  3 says the string certifies nothing whatever its value. Cost if wrong: _check_versions grows a locality
  test it could have got for free.
Ruling: locality is decided from the RESOLVED CLASS's module-name prefix (`_publishable_local_`, from
  discovery._module_name), NOT by calling discover_local a second time. Re-discovery would re-execute
  every user file's top level inside validate, which § Creating a plugin contracts to reach nothing —
  the eager-import exception this slice widens is once per validate, not twice.
Ruling: THREE version lies, not the brief's two. materialize also writes the header comment "Generated
  by `publishable init` from template `<name>` v<TEMPLATE_VERSION>" — core's constant beside a local
  name, the same false claim in prose that the `template_version:` key makes in data. Dropped for local
  templates. `plugin: null` needs no code change, only a pinning test.
Task 10: implemented, commit 6b62b95. 1678 passed + 2 xfailed (baseline 1676). Both new tests carry the
  control the rulings required, in the same test body: generic still warns on a declared-and-differing
  version, and generic still gets both the key and the header version clause. is_local_template lives
  beside _module_name, judged from cls.__module__'s `_publishable_local_` prefix — no re-discovery.
CONTROLLER-VERIFIED, implementer's concern UPHELD: `uv run ruff format --check .` reports 39 of 74 files
  in src+tests would be reformatted, and this is PRE-EXISTING AND REPO-WIDE, not this task's doing —
  20+ of them (artifacts.py, stats.py, units.py, sweep.py, runner.py, test_acceptance.py …) are untouched
  by the whole branch. None of task 10's five files is among them. The implementer was RIGHT to decline
  a mass reformat: doing it inside a feature branch would have buried a 6-file diff under 39 files of
  whitespace and destroyed the review surface. STANDING ISSUE FOR AFTER THE MERGE, not for this slice —
  CLAUDE.md lists `uv run ruff format .` as a project command, and running it as written rewrites more
  than half the tree. Every earlier "ruff format clean" in this ledger meant the TOUCHED files, not the
  repo. Confirmed no task in this branch ran it repo-wide: the branch diff is confined to its own files.
Premise checks for tasks 12-14, done while task 10 was in review (read-only, reference.md):
  Task 12 LIVE: § The importable surface still carries ONE row for all four —
    "`register_template` · `register_resolver` · `register_probe` · `register_writer` | decorator |
    not yet built" — now false for the first. Split needed, exactly as planned.
  Task 13 NARROWER THAN PLANNED: § Package layout's only stale line is
    `templates/{base.py,registry.py,builtin/generic.py}`, which wants `discovery.py`. The `generators/`
    line ALREADY reads "experiment | step | template | report", so generators/template.py needs NO
    layout change — the plan's "if task 2 lands a new file" is the whole of it. Tell task 13's
    implementer not to go looking for a second edit.
  Task 14 CONTEXT: E-TEMPLATE-LOAD's § Errors row and § Templates/§ Creating a plugin already carry the
    eager-discovery and __-prefix prose from tasks 7-8, at four sites. Task 14 touches only
    E-TEMPLATE-UNKNOWN's wording and its "(known: …)" list.
Task 10: review returned. Spec ✅, quality approved-with-findings, none blocking. Reviewer ran FIVE
  mutations independently, two of which the report never ran — including the decisive one (delete the
  locality guard, leaving only the pre-existing falsy branch), which is what ATTRIBUTES the local test's
  pass to the new code rather than to the branch that predates the slice.
Ruling: I OVERRODE THE REVIEWER'S REMEDY on the Important finding. is_local_template infers locality
  from the `_publishable_local_` module prefix, which _module_name applies only to NON-`__` files — so a
  BaseTemplate subclass DEFINED in templates/__helper.py and registered from templates/my_assay.py
  carries __module__ == "__helper", is judged NON-local, and gets core's template_version written and
  compared. Fail-open, in the exact place this task removes that claim. The reviewer weighed two
  remedies (narrow the docstring; derive locality from the registry) and picked the docstring because the
  second costs a get_template signature change across three bindings. THEY DID NOT WEIGH A THIRD, which
  is cheaper than either: stamp the class at `registered = drain_pending()` inside discover_local — the
  one site that already knows the answer — and have is_local_template read the stamp. Correct wherever
  the class was defined, no signature change, no re-discovery, builtins never stamped, and the stamp is
  per-import so nothing carries across repos. GENERALIZES: the module prefix was designed for
  ANTI-ALIASING, not for locality; reusing it as a locality oracle is inference from a scheme built for
  another purpose, and that is where the fail-open came from. Cost if wrong: one attribute and a fallback
  to the docstring narrowing, which the fix round is told to take if the stamp breaks.
Task 10 fix round 1: commit f4c1366. The stamp landed and the helper case is now tested
  (test_a_template_class_defined_in_a_dunder_helper_is_still_local, confirmed failing against BOTH the
  old module-prefix predicate AND a stamp-removed variant). Doc count clause and the init-shaped
  materialize -> validate_config integration test both landed; 1680 passed + 2 xfailed.
Task 10 fix round 2 dispatched. I FOUND A SECOND FAIL-OPEN IN MY OWN REMEDY, one level down, and
  REPRODUCED IT before spending the round. setattr stamps whatever class was registered — including one
  the repo does not own. A templates/*.py that registers a class it merely IMPORTED (core's
  GenericTemplate, or later an installed plugin's) stamps that SHARED class PERMANENTLY, PROCESS-WIDE.
  Probe against f4c1366: `before: generic is_local = False` / `AFTER: generic is_local = True` — one
  discover_local of an unrelated repo, and core's generic gets no template_version and no
  W-TEMPLATE-VERSION for EVERY project in that process. This is the spec's named top trap, "the registry
  becomes process-global while being repo-dependent", and the SAME defect class as the one it replaced:
  a fact recorded on an object that OUTLIVES THE REPO THAT RECORDED IT.
  GENERALIZES, and this is the durable lesson of the whole task: BOTH fail-opens came from answering
  "is this local?" with a proxy — first a module-naming scheme built for anti-aliasing, then an
  attribute on a possibly-shared object. The predicate _is_local(module, templates_dir) — does the
  class's defining file sit under THIS repo's templates/ — was in the file the entire time and answers
  it directly. WHEN A PREDICATE KEEPS FAILING OPEN, THE PROXY IS THE BUG, NOT THE GUARD.
  Fix round told to reuse _is_local rather than write a second answer, and that the helper case must
  keep passing (templates/__helper.py IS under templates_dir). Left the unstamped case's treatment to
  the implementer with one constraint: minimal change preferred, and if it refuses as E-TEMPLATE-LOAD
  the document changes first, since § Templates does not describe that refusal.
Task 10: COMPLETE (commits 6b62b95, f4c1366, e99e50f). 1681 passed + 2 xfailed; ruff check and mypy
  clean. CONTROLLER-VERIFIED the leak is closed by re-running my own probe against the fix:
  `AFTER: generic is_local = False`.
  THE IMPLEMENTER CORRECTED MY RULING A SECOND TIME, and was right again. My fix-round-2 instruction said
  to look up sys.modules.get(cls.__module__) inside discover_local's registration loop. That INVERTS THE
  ANSWER: _import_file restores sys.modules to its pre-import state BEFORE the loop runs, so a genuinely
  local class's module is already gone (-> judged foreign) while an EXTERNAL class like GenericTemplate's
  module is still cached and resolvable (-> judged local). Exactly backwards. It moved the _is_local
  check INTO _import_file, immediately after exec_module and before the cleanup — the only point where
  the evidence still exists — and had _import_file drain and stamp, returning already-correct pairs.
  Mutation `if True:` on the guard fails the leak test and NOT the helper test, which is what proves the
  two cases are distinguished rather than both passing for one reason. Took the minimal option
  (unstamped, not refused) on the judgment call I left open.
  SCOREBOARD FOR THIS TASK: I issued five rulings; two were wrong in the same direction — both proposed
  reading state at a site where the state had already been cleaned up or was shared. The implementer
  probed each before implementing rather than building it as told. That probe-first habit is what kept
  two inverted guards out of the branch.
Tasks 12+13: dispatched BATCHED (sonnet), BASE e99e50f — both are single-line edits to reference.md, so
  one dispatch and one review surface rather than two seats.
Task 14 premise CONTROLLER-VERIFIED live while 12/13 ran (read-only):
  validate.py:517-520 still builds the message `names \`{name}\`, which no installed template registers
  (known: {', '.join(template_names())})` — template_names() called with NO repo_root, so the known-list
  omits every local template, and "no installed template registers" is false for a template installed
  nowhere. Both halves of task 14 are live, and the plan's step-5 mutation (drop the root from the call)
  is exactly the right one.
  template_names() has EXACTLY ONE call site in src/, so task 14's code change is confined to it — worth
  telling the implementer so it does not go hunting for others.
Tasks 12+13: implemented, commits c4a5224 (row split) and 322129e (discovery.py in § Package layout).
  1681 passed + 2 xfailed; ruff and mypy clean. Implementer verified the built/unbuilt claim by ACTUALLY
  IMPORTING all five names rather than reading the table — the right check for a row that asserts
  importability.
Ruling (controller review of 12/13, fix round 1): THE PARAGRAPH DID NOT NEED REWRITING; THE ROW SPLIT
  REPAIRED IT. "A row marked `not yet built` is a promise, not an export. Importing one raises
  ImportError today" was false ONLY WHILE register_template sat inside a row marked not yet built. Once
  the split moves it to a `built` row the sentence is true again, because it DERIVES its claim from the
  Status column instead of restating it. The implementer replaced it with a hardcoded list of the five
  currently-unbuilt names plus "register_template moved off this list once it shipped" — a SECOND SOURCE
  OF TRUTH FOR BUILD STATE (CLAUDE.md's "declared vs derived" drift class) and an undated build fact in
  prose, in the one table whose sanctioned place for build state is the Status column. Concretely: when
  H7b ships register_resolver, the column and the sentence must BOTH be updated and only the column is
  enforced. Told to restore the original wording. Cost if wrong: a slightly terser paragraph.
  GENERALIZES: when a sentence goes false because a TABLE ROW was wrong, fix the row and re-read the
  sentence before rewriting it — a derived claim repairs itself, and replacing it with an enumeration
  converts a self-maintaining statement into a maintenance obligation nobody owns.
Tasks 12+13: COMPLETE (commits 645b4a4, a0d2ab6 — these REPLACE c4a5224/322129e, which the implementer
  unwound with a non-destructive `git reset --soft e99e50f`, both still reachable via reflog). Net diff
  CONTROLLER-VERIFIED as exactly the row split plus the discovery.py line, paragraph byte-identical;
  both new rows carry 4 columns; no trailing whitespace or tabs. 1681 passed + 2 xfailed.
Ruling: NO SEPARATE REVIEWER SEAT FOR 12/13; their independent review is FOLDED INTO THE WHOLE-BRANCH
  REVIEW. Grounds: the net diff is one table row split in two plus one tree line, and I read every line
  of it myself and verified the mechanical properties directly. A fresh reviewer's value here is near
  zero against a full seat's cost, and the whole-branch review reads this diff anyway. Cost if wrong: a
  four-line doc diff reaches the final review unreviewed by a second pair of eyes — bounded, and the
  final review is dispatched on the most capable model. NOT a precedent for code tasks.
Task 14: dispatched. BASE a0d2ab6.
Task 15 premise CONTROLLER-VERIFIED while task 14 ran (read-only). The greenfield-refusal family is
  FOUR codes in src/ — E-STEP-EXISTS, E-EXPERIMENT-EXISTS, E-PROJECT-EXISTS, E-TEMPLATE-EXISTS — and
  § Exit codes names EXACTLY ONE of them ("A creation command refusing to overwrite an existing file
  reports `E-STEP-EXISTS` and exits `1`"). The other three appear in NO tracked document. E-TEMPLATE-
  EXISTS (minted in task 9) is therefore the fourth undocumented-ish member, not a novel omission —
  which is precisely why step 2c generalizes the clause to the family instead of adding rows.
  DO NOT fold E-ARTIFACT-EXISTS into that generalization: it is a DIFFERENT rule (io.write/io.path onto
  an existing target at RUN time, carrying ArtifactExistsError) and it already has its own § Errors row.
  The family clause covers creation commands refusing to overwrite, which is four codes, not five.
Task 14: implemented, commit 24da5fc. 1682 passed + 2 xfailed. Message now names the three homes and
  calls template_names(repo_root); test uses DISTINCT names (local `cohort_local`, unknown
  `not_anywhere`) so no assertion can pass on the interpolated unknown name — the exact coincidence trap
  the brief warned about. Implementer also found and fixed a THIRD stale site nobody had scoped:
  § The one config file said experiment_type "must resolve to one an installed package registers".
MY BRIEF WAS TOO NARROW AND THE IMPLEMENTER CAUGHT IT. I told it "template_names() has exactly one call
  site in src/, your change is confined to it". True of template_names, FALSE of what the task needed:
  E-TEMPLATE-UNKNOWN has TWO EMIT SITES, and generators/experiment.py:55 still raises "no installed
  template registers". GENERALIZES: I scoped the task by the HELPER it calls rather than by the CODE it
  emits. A diagnostic's unit of work is every site that raises or reports its code, because § Errors
  carries ONE ROW PER CODE — scoping by helper let a second emitter drift out from under the row I had
  just rewritten.
Ruling: fixed INSIDE task 14, not routed onward. The implementer proposed routing (it is a raise at
  generate time, not a validate finding, and outside the brief's file list) — defensible, but the § Errors
  row is per CODE, not per emit site, so routing would ship a row describing one of two messages while
  the other states a guarantee the build does not provide. Worth recording: that site ALREADY passes
  repo_root correctly (task 5 wired it), so a local template resolves there today — the code was right
  and only the message was wrong, which is why nothing failed. Cost if wrong: one message and one test
  land a slice earlier than scoped.
Task 14: complete pending review (commits 24da5fc, d972d21). 1683 passed + 2 xfailed. Second emit site
  in generators/experiment.py now carries the identical message AND a (known: …) list. Implementer went
  beyond the brief twice, both defensible: fixed § The one config file's "must resolve to one an
  installed package registers", and reworked the § Errors row toward stating the CONDITION rather than
  the message text, citing that section's own governing rule "Each row states the condition, not the
  wording" — a rule I had not pointed it at. Confirmed no third emit site.
Task 14 review dispatched (opus). BASE a0d2ab6, HEAD d972d21. Asked specifically whether anything PINS
  the two messages as identical — if each test hard-codes its own copy of the string, they can drift
  apart with both tests green, which is a dimension no assertion can see.
Task 15 dispatched (sonnet) IN PARALLEL with task 14's review. BASE d972d21. Sections are disjoint —
  task 15 owns § Creating a plugin, § The generated README, § Generators, § Exit codes, § Templates;
  task 14's review may revisit § Errors and § The one config file, and task 15 is told to stay out of
  both. If 14's review yields fixes they land AFTER task 15's commit; only a fix round edits files, and
  a reviewer does not.
Task 15: implemented, commit 075455e (docs/reference.md only). All four items landed — the widened
  entry-point promise in § Creating a plugin, the README gap plus required_env's deadness (grep-verified)
  in § The generated README, § Exit codes' greenfield clause widened to all four codes with
  E-ARTIFACT-EXISTS explicitly excluded, and the __pycache__ sentence in § Templates.
MY SCHEDULING ERROR, and it corrupted a test run. I dispatched task 14's REVIEWER concurrently with
  task 15's IMPLEMENTER in the SAME WORKING TREE, having judged conflict risk by DOCUMENT SECTION. That
  was the wrong axis: A REVIEWER MUTATES SOURCE FILES to run mutation tests. Task 15 ran the suite while
  the reviewer had a live mutation in generators/experiment.py and saw 1 failure it correctly diagnosed
  as not its own and correctly refused to touch. Tree verified clean afterwards, suite green at 1683 + 2
  xfailed, both commits sound. GENERALIZES: NEVER run a reviewer and an implementer concurrently in one
  worktree, whatever they nominally touch — mutation testing writes to arbitrary source files, so the
  only safe parallelism is across separate worktrees. Cost here was one confusing suite run and no
  damage, purely because the implementer diagnosed it rather than "fixing" it.
Task 14 review: spec ✅, approved with findings. Both out-of-brief edits upheld. TWO IMPORTANTS sent as
  fix round 2:
  (a) NOTHING PINS THE TWO MESSAGES IDENTICAL — proved by mutating only generators/experiment.py, which
  fails exactly one test while validate.py's copy is never consulted. Each test hard-codes its own
  literal. Worse: the test is NAMED ..._message_matches_validates and its docstring says the wording must
  agree — A TEST ASSERTING A GUARANTEE IT DOES NOT PROVIDE, this repo's most repeated defect class, sited
  in the one artifact whose job is to catch it. A reader greps for "is this checked?", finds that name,
  and stops looking.
  (b) The new row says two surfaces RAISE the code, naming validate — which is contracted to COLLECT and
  never raise, per its own comment eight lines above the emit site, and per § Errors having separate
  "core raises" and "validate reports" sections.
Ruling: task 15's out-of-scope concern #2 is NOT A DEFECT. It flagged § Secrets & credentials claiming
  "validate confirms each is set" for required_env/requires_env while src/ has zero os.environ/getenv/
  dotenv calls. Verified the absence — but secrets.py is marked "not yet built" in § Package layout, so
  that sentence is a SPEC CLAIM in the present tense about an unbuilt module, which is exactly the
  sanctioned pattern this repo uses everywhere. Contrast with what task 15 correctly DID record:
  BaseTemplate.required_env is a member users can DECLARE TODAY whose reader is unbuilt — a live
  declarable surface with no effect, which is a different and real gap. THE DISTINCTION: an unbuilt
  reader of an unbuilt surface is spec; an unbuilt reader of a SHIPPED surface is a defect.
Task 14: COMPLETE (commits 24da5fc, d972d21, e9eaa71). 1684 passed + 2 xfailed; ruff and mypy clean.
  The message-drift fix is the right shape: registry.unknown_template_message(name, repo_root) is now the
  SINGLE construction, both surfaces call it, and the test drives BOTH from one repo and asserts the LIVE
  OUTPUTS EQUAL EACH OTHER rather than each comparing to its own literal. Proved by mutating one site
  back to a divergent hard-coded string and watching the equality assertion fail. That converts the
  guarantee the test's NAME had been claiming into one it actually provides.
  Minor 4 also closed with a new test: a missing or empty experiment_type is the same unknown-template
  condition, and the row now says so.
Task 15 fix round dispatched (M4 only): § Creating a plugin's "Four registries, one mechanism" paragraph
  still says validate "reports a config naming one that no installed package registers" — incomplete for
  templates now that one can be installed nowhere. Told to qualify WITHOUT restructuring the paragraph
  around the exception, and WITHOUT duplicating § Templates' three-homes sentence. Also warned that the
  adjacent entry-point sentence's `plate_wells` example is a RESOLVER, for which the claim remains
  exactly true — an edit must not make a correct sentence read as wrong.
  RUN SEQUENTIALLY this time. Nothing else against the tree.
Task 15: COMPLETE (commits 075455e, 6468842). Single-sentence qualification, framing and the adjacent
  plate_wells resolver example both left intact.
ALL 15 TASKS COMPLETE. Branch h7a-local-templates: 26 commits off 4681bda, 13 files, +2199/-55.
  1684 passed + 2 xfailed; ruff check and mypy clean; tree clean. Whole-branch review dispatched (opus).
WHOLE-BRANCH REVIEW (opus): findings — 0 Critical, 3 Important, 5 Minor. Shipped behaviour verified
  CORRECT END-TO-END rather than read: generate template -> init -> validate -> run with the local
  template's aggregate metric landing in run.yaml; two repos in one process; collision and shadow both
  refused naming both providers; a broken file a finding. Brief items 3 and 4 — which NO TASK TESTED —
  hold: code_hash moves on a templates/ edit and returns on revert, run refuses a dirty templates/ with
  E-CODE-DIRTY, and the scaffolded .gitignore keeps __pycache__ out of both gates.
  IMPORTANT 1: validate imports every templates/*.py TWICE on the unknown-name path, and the second is
  OUTSIDE THE TRY. Task 14's unknown_template_message(name, repo_root) re-enters discover_local —
  violating the task-10 ruling I recorded ("once per validate, not twice"), whose whole point was that
  eager import re-executes arbitrary user top-level code. A ContractError from the second call escapes
  validate_config, which is contracted never to raise, discarding every other finding in the pass.
  MY OWN RULING WAS BROKEN BY A LATER TASK AND NO PER-TASK REVIEW COULD SEE IT — task 14's reviewer had
  no reason to count discovery calls. This is exactly the cross-task seam a whole-branch review is for.
  IMPORTANT 2: "a collision among the files that did load is still found rather than masked" is FALSE,
  asserted in discover_local's docstring, in reference.md's E-TEMPLATE-LOAD row (NORMATIVE), and in a
  test docstring. raise load_faults[0] precedes the collision loop; claims is computed and discarded.
  Ruled: CODE IS RIGHT, THE THREE PASSAGES ARE WRONG. The spec's argument for load-first — a collision
  verdict computed while a file failed to load is computed over a PARTIAL SET OF CLAIMS — is sound, and
  the false sentence CONTRADICTS THE VERY ARGUMENT THAT JUSTIFIES THE ORDERING. Written as if both
  properties could hold at once; they cannot.
  IMPORTANT 3: two documented ordering guarantees have no test that can fail — sorted(claims) reversed,
  and the sorted directory walk reversed, each leave 1684 passing. Every fixture has EXACTLY ONE
  colliding name and EXACTLY ONE broken file. Ruled: FIX THE FIXTURES FIRST, then the assertions — the
  defect is fixture content, not missing asserts.
Single fix dispatch sent (opus), per the skill's one-fix-one-re-review rule for final findings.
WHOLE-BRANCH FIX ROUND complete: 6d2de98, 6d5822e, b4941e6, 8403a6b, 761838f, c0df967. All 3 Importants
  and all 5 Minors closed. 1689 passed + 2 xfailed (1684 + 5 new); ruff and mypy clean; ruff format
  compared PER FILE against 6468842 — identical pass/fail set, nothing newly unformatted.
  I1 fixed by registry.resolve_template(name, repo_root) -> (template, known): one merge, one discovery,
  with unknown_template_message(name, known) still the single source of the wording.
  THE FIXER CAUGHT A NEAR-MISS THE REFACTOR CREATED: test_a_template_cross_field_rule_is_reported
  monkeypatched validate_mod.get_template, which resolve_template no longer references — the patch would
  have become a SILENT NO-OP and the test would have kept passing while testing nothing. Repointed and
  proved it still bites. A refactor that reroutes a call can silently defuse every monkeypatch aimed at
  the old name; grep the patch targets whenever you move a call site.
  I3: MY RULING SAID "TWO COLLIDING NAMES" AND TWO IS NOT ENOUGH. The fixer proved it — with two names
  the reverse of the insertion order IS the sorted order for one arrangement, so its first fixture left
  `reversed(list(claims))` green. Three names (zzz, aaa, mmm) give three distinct answers under insertion
  order, its reverse, and name order, so both mutants die. GENERALIZES: to distinguish N candidate
  orderings a fixture needs enough elements that all N produce DIFFERENT answers — counting the orderings
  is the design step, and two elements only ever distinguish two.
  I2: the fixer REJECTED the reviewer's proposed replacement clause ("still computed over a complete set
  of claims") because under a load fault NO collision verdict is computed at all — correct, and it also
  found a FOURTH site the review missed in the same docstring.
  M3: the fixer judged the REVIEW'S DIAGNOSIS WRONG IN ITS HARM — the "next repo inherits the buffer"
  chain is unreachable since every discover_local drains before its loop. Re-scoped to the real defect:
  an unconditional promise over a conditional path.
Residual concerns recorded, NOT fixed in this slice (adjudicated):
  (a) A `run` still performs TWO local discoveries — validate's plus cli.py's own get_template in the
  finalize path. Distinguishing argument for leaving it: the once-per-validate ruling rests on § Creating
  a plugin contracting VALIDATE to reach nothing, and `run` executes user code by definition, so the
  contract does not bind there. Worth its own ruling in H7b; not a correctness defect, since each
  discovery is a fresh snapshot-restored import.
  (b) registry._merged's sorted(local) is unfalsifiable while core ships exactly one builtin.
  (c) Nothing tests the code_hash-vs-dirty-gate split that M1 now documents; the whole-branch reviewer
  verified it by hand.
Scoped re-review dispatched (opus), BASE 6468842, HEAD c0df967.
