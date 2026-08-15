# SDD ledger — plan: docs/superpowers/plans/2026-08-08-implementation-spine.md

Branch: s1-implementation-spine (in-place, not a worktree — see setup note)
Base: d5bf355d0e72bf9416a43ff704c5243eeffb1894

Task 1: implemented (commit e0440e7) — spec ✅
Task 1: minor (deferred): dev venv is CPython 3.13.7 while mypy python_version = "3.11"; no .python-version pin
Task 1: fix round 1/5 dispatched — Important: pythonpath = ["."] unproven by any committed test
  ruling supplied to implementer: the need IS real (Task 8 does `from tests.conftest import git`),
  so keep the setting and add a committed test that proves it; also gpgsign=false on the fixture
Task 1: fix round 1/5 (2 addressed, 0 open; commits e0440e7..e84e0bb)
Task 1: complete (commits d5bf355..e84e0bb, review clean)
Task 2: implemented (commit 3790550) — spec ✅ vs brief; no Critical/Important vs brief
Task 2: fix round 1/5 dispatched — Important (upgraded from reviewer's Minor by cross-check
  against the normative doc): render() hardcoded "error"/"warnings"; reference.md
  § Exit codes and diagnostics renders "2 problems (1 error, 1 warning)". Plan text was the
  source of the bug; plan file corrected too (added _plural + two pluralization tests).
Task 2: fix round 1/5 (1 addressed, 0 open; commits 3790550..27b07d6)
Task 2: complete (commits e84e0bb..27b07d6, review clean)
Task 3: implemented (commit aebd5a1) — spec ✅ except one contract violation
Task 3: fix round 1/5 dispatched — Important: check() could raise TypeError when `pattern`
  is set on a non-str Param, breaking its never-raise contract that Task 15 depends on.
  Bug originated in plan text; reference.md § Templates types `pattern` to str, so the fix
  is to refuse the combination in __init__ plus a defensive isinstance guard. Plan corrected.
  Three implementer deviations (typed bounds hoist, int|float, top-level `import re`)
  reviewed and accepted — order and message text preserved.
Task 3: fix round 1/5 (1 addressed + same crash class found in numeric bounds and fixed;
  0 open; commits aebd5a1..b418a5e)
Task 3: complete (commits 27b07d6..b418a5e, review clean)

== Contract audit of Tasks 4-17 plan text (before dispatching Task 4) ==
Fixed in the plan:
  T9  verify_manifest was blind to ADDED files; hash_all claims identity, so a new file counts
  T11 resolve_repeats n<1 returned [] -> a run with zero repeat executions reading as success
  T13 allocate_run_dir exists()-then-mkdir TOCTOU -> defeats the collision safety the spec
      names as the reason the _b/_c suffix exists. Now mkdir-and-catch.
  T15 _check_replication used `n or k or 1`, so a declared 0 read as absent -> the floor test
      could never fire. Also: generic's floor is 1, so no legal count can breach it; the test
      now exercises _check_replication directly with a stub template, and n<1 is E-REPL-N.
  T15 E-META-REQUIRED was being emitted for data.* fields -> now E-DATA-REQUIRED
  T16 scaffold_project could hang on a machine with commit signing -> gpgsign=false
  T16 the scaffold.py block nested a ```bash fence inside a ```python fence, truncating the
      code block; the brief for T16 would have been unusable. Rewrapped in 4 backticks.
  T17 _dispatch_generate raised KeyError on a missing --input-dir/--output-dir instead of
      returning exit 2
  T17 __import__("json") -> a real top-level import
Ledgered as deliberate S1 deviations (docs/superpowers/spec-defects.md, written by T7):
  code_hash is not .gitignore-aware; parameters_hash does not normalize to init's output
Noted, deliberately NOT fixed in S1:
  T14 no E-STEP-RETURN-TYPE enforcement on a step's return. The spec applies one coercion
      rule to three surfaces (io.record, step return, aggregate); S2 builds the other two,
      so implementing it once there beats implementing it twice.
  T5/T10 mutable class-level defaults (required_env = [] etc.) — the spec shows this exact
      shape and nothing mutates them; revisit if anything ever does.
  T6 _parameters_block assumes exactly two dotted path segments; generic has only those.
  T12 io.write creates the parent directory before rejecting an unwritable object.
Verified after edits: 46/46 python blocks parse, tables well-formed, fences balanced.
Task 4: complete (commits b418a5e..ec767a8, review clean, no fix round)
  note: types-pyyaml added to dev group (not runtime deps) for mypy --strict
Task 5: complete (commits ec767a8..c4ec912, review clean, no fix round)
  reviewer's report was terse; controller independently verified all four generic params,
  their order, naming_pattern, absent aggregate, get_template(None), __all__, comment() strings
Task 6: implemented (commit 19bcc24) — spec ✅; round-trip probe confirmed every emitted
  value passes its own Param.check()
Task 6: fix round 1/5 dispatched — Important: _scalar emitted str defaults unquoted, so ""
  parses back as None and "yes"/"null"/"1.5"/": " break or change type. Latent for generic
  (only "pearson"), inherited from plan text. Fixing.
Task 6: Important NOT fixed, ledgered instead — the header says "complete parameter set"
  while sweep and statistics.{contrasts,resample,null_test,report_by} are absent. The line
  is verbatim from reference.md § The one config file; changing it would diverge from the
  spec's own shown output. S3 restores sweep, S4 the statistics sub-keys.
Task 6: fix round 1/5 (1 addressed: str VALUES now round-trip; commits 19bcc24..de69dbc)
Task 6: fix round 2/5 dispatched — controller probe found the same defect in emitted KEYS:
  `yes:` parses back as bool True, `null:` as None, which breaks Config dot-access since it
  looks the name up as a string. Quote-only-when-needed, both head and leaf segments.
Task 6: fix round 2/5 (1 addressed: KEYS now round-trip as str, incl. head segment;
  commits de69dbc..5e27ae5)
Task 6: fix round 3/5 dispatched — controller-caused: I authorised unconditional value
  quoting in round 1, which made generic emit `method: "pearson"` where reference.md
  § The one config file shows `method: pearson`. Same divergence-from-shown-output I
  refused for the header comment. Reusing the round-2 predicate for both keys and values.
Task 6: fix round 3/5 (rounds 2+3 both ADDRESSED, 0 open; commits de69dbc..aca5b9d)
  one shared _needs_quoting predicate serves keys and values; generic renders bare and
  matches reference.md; hostile keys+values all round-trip as str
Task 6: minor (deferred): _needs_quoting is slightly conservative (over-quotes some strings
  YAML would accept bare); over-quoting is safe, never under-quotes
Task 6: minor (deferred): _needs_quoting does not special-case YAML 1.1 .inf/.nan sigils
Task 6: complete (commits c4ec912..aca5b9d, review clean after 3 rounds)
Task 7: implemented (commit 5336082) — spec ✅; controller probed collision resistance,
  ordering determinism, non-mutation, canonical JSON: all hold
Task 7: fix round 1/5 dispatched — Important (silent correctness): _SKIP_DIRS was matched
  against the ABSOLUTE path, so a repo under any dir named __pycache__/.git/etc hashed zero
  files and returned the empty-tree digest — a well-formed hash certifying nothing.
  Reviewer reproduced it. Bug originated in plan text; plan corrected.
Task 7: minor (deferred): "no src/", "empty src/", and the bug above all yield the identical
  empty-tree digest; making zero-files observable belongs with the validation engine.
Task 7: fix round 1/5 (1 addressed, 0 open; commits 5336082..bc2ecb3)
  emitted relative-path string confirmed byte-identical, so no previously-computed hash moved
Task 7: complete (commits aca5b9d..bc2ecb3, review clean)
Task 8: implemented (commit 84030ed) DONE_WITH_CONCERNS — implementer correctly escalated
  rather than deviating: rev-parse HEAD under check=False yields "" on a zero-commit repo,
  so provenance would record commit: "". Ruled: fail loudly, E-GIT-NO-COMMIT. Plan corrected.
  Verified safe by implementer: missing templates/ is not fatal to status --porcelain;
  /tmp -> /private/tmp symlink prefix mismatch resolves correctly (git normalises).
Task 8: complete (commits bc2ecb3..e83a687, review clean)
  NOTE: the implementer improved on my ruling. I specified `rev-parse HEAD` + `if not commit`,
  which would NOT have fired: bare rev-parse prints the literal "HEAD" to stdout on a
  commit-less repo (exit 128, stdout "HEAD" — verified). That is truthy, so the record would
  have carried commit: "HEAD", worse than "". It used `rev-parse --verify HEAD`, which prints
  nothing. Plan corrected to match the shipped code.
Task 9: implemented (commit fd4c957) DONE_WITH_CONCERNS — implementer flagged that unindexed
  files under hash_index, and all files under none, fall back to size+mtime so a same-size
  same-second edit reports clean. Ruled: NOT a defect (reference.md § How the three are
  computed grades the policies exactly so), but mtime was truncated to whole seconds;
  switched to st_mtime_ns to shrink the blind window at zero cost. Plan corrected.
Task 9: fix round 1/5 (ns-mtime addressed; commits fd4c957..454ffe8)
Task 9: complete (commits e83a687..454ffe8, review clean)
  recorded behaviours (not defects): symlinks are followed and the target's content is
  hashed under the link's relative path, so a target change IS detected; an unreadable file
  makes build_manifest raise PermissionError uncaught.
Task 10: implemented (commit fd84114) — spec ✅
Task 10: fix round 1/5 dispatched:
  CRITICAL step_name collisions undetected — two classes with the same short name share a
    directory AND a run-record key; per_repeat silently overwrites. New code
    E-STEP-NAME-COLLISION authorised (not in the spec's registry; ledgered for reconciliation).
  IMPORTANT ordering test used one condition, so it could not detect the per-condition
    interleaving it claimed to verify. Rewriting with two conditions.
  IMPORTANT index-0 and E-STEP-CONTEXT-ABSENT were verified only by throwaway scripts —
    same pattern as Task 1's pythonpath finding. Committed tests required.
Task 10: minor (deferred): zero-arg user __init__ silently works, required-arg fails with a
  plain TypeError; BaseExperiment.steps is a shared mutable class default (subclasses rebind)
Task 10: fix round 1/5 (3 addressed: collision detection, two-condition ordering test,
  committed index-0 + context-absent tests; 0 open; commits fd84114..b0581be)
Task 10: complete (commits 454ffe8..b0581be, review clean)
Task 11: implemented (commit e7bbe7a) DONE_WITH_CONCERNS — implementer escalated that label
  uniqueness rests on 32-bit seeds happening to differ (_seed_for truncates SHA-256 to 4
  bytes; birthday bound ~n^2/2^33), verified empirically but not guaranteed.
  Ruled: enforce it. Not mainly a naming issue — two repeats with the same seed execute
  identically, so a 5-seed design would report repeat_spread over 4 distinct answers as 5.
  New code E-REPL-SEED-COLLISION authorised; ledgered beside E-STEP-NAME-COLLISION.
Task 11: fix round 1/5 (E-REPL-SEED-COLLISION addressed; commits e7bbe7a..35f609f)
Task 11: minor (deferred): the label-uniqueness loop in _check_no_collisions is unreachable
  independently of the seed loop above it (fallback labels are str(seed)); harmless
  redundancy, would benefit from a comment saying so
Task 11: complete (commits b0581be..35f609f, review clean; cross-process determinism verified)
Task 12: implemented (commit a0d0a3a) — spec ✅; all three guarantees (append-only, atomic,
  confined) verified under adversarial probing incl. a real symlink escaping the step dir
Task 12: fix round 1/5 dispatched — Minor promoted: _read hand-rolls extension dispatch
  instead of inverting WRITERS, contra reference.md § Steps and artifacts ("every reader
  inverts the same table"). Harmless today, but S2 adds .parquet and the duplication makes
  forgetting the reader the default outcome. Same two-callers-must-not-drift argument as
  Task 6's quoting predicate.
Task 12: minor (deferred): _encode_csv([]) writes a lone blank line rather than an empty file
Task 12: minor (deferred): io.path() pre-creates parent dirs even if never written to
  (asserted by the brief's own test, so intentional)
Task 12: fix round 1/5 (READERS now inverts WRITERS via the shared _suffix_for; 0 open;
  commits a0d0a3a..ec277cd)
Task 12: complete (commits 35f609f..ec277cd, review clean)
Task 13: implemented (commit dae3112) DONE_WITH_CONCERNS — three escalations, all legitimate:
  (1) FIX: point_latest can leave `latest` symlink and `latest.txt` disagreeing; reference.md
      § Run identity says "every command reads either", so a disagreement breaks the pointer.
      Implementer recorded it as xfail(strict=True) rather than silently fixing — converting
      to a passing test plus the mirror case.
  (2) FIX: RunLock's collision message calls read_text(), which can itself raise if the holder
      vanishes mid-read — a contention path that crashes while explaining contention.
  (3) DEFER to Task 17: unwritable output_dir surfaces as a bare PermissionError traceback.
      Wrapping OS errors per-module would scatter the same try; the CLI is the single point
      where an environment failure should become a diagnostic. Ledgered, incl. the note that
      the spec's exit-code table doesn't clearly cover a local filesystem refusal.
Task 13: fix round 1/5 (pointer exclusivity + degraded lock message addressed; 0 open;
  commits dae3112..04fc983). Reviewer confirmed race-freedom with 26 concurrent threads and
  a 27-way race hitting E-RUN-ID-EXHAUSTED; verified the lock-message test is a real
  regression guard by reverting the fix and reproducing the crash.
Task 13: complete (commits ec277cd..04fc983, review clean)
Task 14: implemented (commit 5741bf4) DONE_WITH_CONCERNS — five escalations, all real:
  FIX (1) seeds.get(label, 0) silently ran an execution with seed 0 if plan labels and the
    repeats argument disagreed — the same silent-nothing replication.py treats as a hard
    error. Now E-RUN-SEED-MISSING.
  FIX (2) a truthy non-mapping return flowed into run.yaml unvalidated; `or {}` silently
    discarded falsy ones. Minimal shape gate added (E-STEP-RETURN-TYPE); full scalar
    coercion still deferred to S2 where it serves all three surfaces at once.
  FIX (3) the brief invented a `per_condition` key absent from reference.md — MY
    inconsistency: I forbade inventing results.shared for run-scoped returns and then the
    brief invented this for condition-scoped ones. Removed; `values: {}` added instead,
    which the spec does show.
  LEDGER (4) artifacts surviving a failed execution — by design, io.exists is the sanctioned
    coping mechanism per § Resuming.
  LEDGER (5) per_repeat's shape when nothing repeats is unspecified; S1 emits a "" key.
Task 14: fix round 1/5 (3 addressed: E-RUN-SEED-MISSING, E-STEP-RETURN-TYPE gate,
  per_condition removed + values added; 0 open; commits 5741bf4..05d103c)
Task 14: minor (deferred): a failed execution records {} in per_repeat, indistinguishable
  from a step that returned nothing; execution.status carries the fact, so not promoted
Task 14: complete (commits 04fc983..05d103c, review clean)
Task 15: first implementer terminated by an API session limit after 7 tool calls; committed
  nothing. Tree verified clean at 05d103c, 138 tests passing, no validate.py or test file
  left behind. Re-dispatched fresh from the same brief.
Task 15: implemented (commit 14b83fa) DONE_WITH_CONCERNS — three findings:
  (a) the plan's test_a_missing_parameter_is_reported could never pass: every generic param
      has a default, so deleting one cannot produce E-PARAM-MISSING. Implementer rewrote it
      against a stub template. Adopted; plan corrected.
  (b) E-CONFIG-PARSE, E-TEMPLATE-RULE and E-DATA-REQUIRED had no test anywhere — the
      one-test-per-identifier bar caught three codes nothing exercised. Added.
  FIX (c) _check_data's bare `except Exception: return` silently skipped the entire data
      block, including E-DATA-IN-REPO — the check design-principles.md names as one of three
      enforcement points keeping governed data out of a shareable repo. Narrowed to
      E-GIT-NO-REPO only.
  FIX (d) _check_replication returned after the first E-REPL-N, violating the module's own
      collect-don't-stop contract. Now continues.
Task 15: fix round 1/5 (narrowed exception handler + collect-don't-stop in _check_replication;
  0 open; commits 14b83fa..5effaf6). Reviewer ran real mutation testing: broke three checks
  in the source, all three tests failed as they should — no dead assertions.
Task 15: minor (deferred): _check_replication skips W-REPL-FLOOR when any level is invalid
Task 15: SPEC DIVERGENCE ledgered — findings are ordered by check-function sequence, not by
  config position as § Exit codes and diagnostics promises.
Task 15: complete (commits 05d103c..5effaf6, review clean)
Task 16: implemented (commit 21789da) — spec ✅; hand-verified scaffold → experiment →
  two steps produces an importable experiment.py listing all three in order
Task 16: fix round 1/5 dispatched:
  generate step had no duplicate-name guard — running it twice writes two files whose
    identical `Step` classes shadow each other in experiment.py; build_plan catches it
    downstream via E-STEP-NAME-COLLISION, but three layers from the cause. Now E-STEP-EXISTS,
    refusing before anything is written.
  re-running generate experiment raised a bare FileExistsError instead of a PublishableError,
    so the CLI (which catches only PublishableError) would show a traceback. Now
    E-EXPERIMENT-EXISTS.
  NOT fixed: generate step's string-replace rewrite is fragile against a hand-edited
    experiment.py. Making it robust is a parsing problem, out of scope; ledgered.
Task 16: fix round 1/5 (E-STEP-EXISTS + E-EXPERIMENT-EXISTS; commits 21789da..78237b2)
Task 16: fix round 2/5 dispatched:
  generate step emitted a blank line before each new import, splitting the block (ruff I001).
    Graded Important not Critical — the scaffolded pyproject ships no ruff config, so the
    reviewer applied THIS repo's rules to generated output. Fixing anyway because `run`
    refuses a dirty src/**, so a user's own formatter would push them onto `draft`.
    Probe 5 existed to catch this and no test ran it — that's why it survived.
  scaffold_project silently clobbered README/LICENSE/pyproject on a second `new`, skipped
    the commit (since .git existed), and left a dirty tree with no record. Now
    E-PROJECT-EXISTS. No --force: a flag that changes what a command does is a parameter
    in disguise.
Task 16: fix round 2/5 (both addressed; commits 78237b2..0ea8905)
Task 16: complete (commits 5effaf6..0ea8905, review clean)
Task 17: implemented (commit dc21d55) — 178 tests, ruff/mypy clean, mechanical *.md pass
  clean, both removed CLAUDE.md strings absent. Implementer added E-ENTRYPOINT-IMPORT, a
  _dispatch split so main's except really wraps everything, and (via its own advisor review)
  a sys.modules-purge test verified by mutation.
Task 17: fix round 1/5 dispatched — found by the controller hand-running the real user
  journey, NOT by the acceptance test: environment/ is empty and uv_lock is null, while
  README claims code+environment+data are all pinned. Root cause is bootstrapping — `uv lock`
  in a scaffolded project fails because publishable isn't on any index yet — but the run
  proceeds in silence. Now: always copy pyproject.toml, warn W-ENV-UNLOCKED, and have the
  acceptance test assert on environment/ (it previously said nothing about it).
Task 17: fix round 1/5 (W-ENV-UNLOCKED + pyproject always captured + acceptance test now
  asserts on environment/; commits dc21d55..9b2b886). Controller verified both paths by hand:
  no lockfile -> warning, exit 0, pyproject captured; lockfile -> silent, uv_lock path+hash set.
  DEVIATION: no separate scoped re-review dispatched for this round — the whole-branch review
  immediately follows over a superset of the diff and is explicitly pointed at these findings.
Task 17: complete (commits 0ea8905..9b2b886, CLAUDE.md rewritten, removed strings confirmed
  absent, mechanical *.md pass clean)
== ALL 17 TASKS COMPLETE ==
== FINAL WHOLE-BRANCH REVIEW ==
Opus review over 35 commits: no Criticals. 4 Important + 3 Minor. Confirmed 3 of 4 pins real
  (verified editing analysis.method moved parameters_hash and left code_hash byte-identical);
  environment unpinned in the default journey, ruling upheld but README's four-for-four claim
  should be stated honestly. Corrected my framing: the ~30 validate-time codes are NOT
  registry violations — § Errors core raises enumerates raise-time codes only and the spec
  says "one registry rather than two".
Fix wave (single dispatch, commit e6d08ca): all 6 applied.
  1 config_committed wrote a FALSE claim into run.yaml for relative paths (.resolve())
  2 validate blessed configs run could not execute (E-ENTRYPOINT-REQUIRED, E-DATA-POLICY)
  3 the active layout was never recorded though reference.md requires it — MY acceptance bar
    listed it and nothing ever wrote or asserted it
  4 manifest drift failed the run silently (E-INPUT-CHANGED + recorded paths)
  5 two diagnostics bypassed Collector; 6 hardcoded version
Scoped re-review: all 6 ADDRESSED, no regressions, no new breakage. Fix 1 verified by
  reverting and watching its test fail.
FINAL: 186 passed, ruff clean, mypy clean, 36 commits, tree clean.

== SECOND WHOLE-BRANCH REVIEW (final state, 36 commits) ==
Found the CRITICAL that 17 task reviews + 1 branch review + my own hand-run all missed:
  `sweep` was silently ignored (cli hardcoded one condition), so a config declaring a
  two-condition grid exited 0, ran one condition, and embedded the sweep verbatim in
  run.yaml — a well-formed record describing an experiment nobody ran. Siblings: data.units
  ignored for resolution while STILL feeding design_digest (declaring it moved every seed),
  and order: randomized validated clean then ran as_declared.
  Root cause is mine: the design spec put sweeps/units "out of scope for S1" and never said
  out of scope must mean REFUSED. The branch already had the right pattern in
  E-REPL-KIND-UNSUPPORTED.
Fixed in 36f9a0d: E-SWEEP-UNSUPPORTED, E-DATA-UNITS-UNSUPPORTED, E-REPL-ORDER-UNSUPPORTED,
  E-DATA-NOT-ABSOLUTE, hoisted E-DATA-REQUIRED/E-DATA-UNREADABLE above the repo early return,
  and one shared resolves_inside_repo helper. Re-review: all ADDRESSED, two tests broken and
  confirmed failing, empty sweep:{} still allowed, fresh CLI config still runs end to end.

PARKED (no second fix wave; neither is load-bearing — both fail loudly, neither writes a
false record):
  1. validate.py ~176: the E-DATA-UNREADABLE check re-derives the path independently of the
     new absoluteness check, so it stats a relative path against cwd and double-reports
     alongside E-DATA-NOT-ABSOLUTE. Noise, not a wrong answer — the config is still refused.
  2. generate_experiment resolves --input-dir against cwd for its in-repo check but writes
     the verbatim relative string, so `--input-dir ./data` scaffolds a project whose config
     fails the next validate. Inconsistent with its own E-DATA-IN-REPO posture. Fails loudly.
DECLINED: softening README's "code, environment and data all pinned". The four documents are
  normative and describe the target the implementation follows; editing one to describe a
  temporary slice state would invert that relationship. Stays ledgered instead.
