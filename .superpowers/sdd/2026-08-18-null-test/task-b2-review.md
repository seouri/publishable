# Batch 2 review: tasks 5+24, 6, 7, 8, 9

Reviewed at `e0b4d18` on branch `h4d-null-test`, 2026-08-19. Gates re-run by me at that commit:
`ruff check` clean, `ruff format --check` 80 files, `mypy` 45 source files clean,
`uv run pytest` **2297 passed, 1 skipped, 2 xfailed**. Four prescribed mutations re-run against the
full unfiltered suite and reverted by editing the source back; sources verified byte-identical to a
pre-mutation copy, `git status --porcelain` empty, `__pycache__` cleared, suite re-run green after.
**The tree is clean apart from this review file itself**, which shows as `??` — worth one clause,
since that proves `.superpowers/sdd/.gitignore` is not currently clobbered to a bare `*`.

## Verdicts

**Spec compliance: PASS with two Majors.** Every code the batch minted is emitted, distinguishable and
alive alongside `E-STATS-NULLTEST-UNSUPPORTED`; the closed schema keeps its outer `dict` entry; the
floor, the enum, the union and the derived level all match the design's § Corrections. Major 1 is an
interaction the design does not rule on: task 7's group-axis union and task 9's roster-attribute
level derivation compose into a silent fail-open, demonstrated end-to-end. Major 2 is the other end
of the same function: § Validation's *Null test coherence* row says `null_test` **requires**
`shuffle`, and no check enforces presence.

**Task quality: PASS, high.** The blindness claim is correct and I could not overturn it; the
docstring trim is exemplary; the discriminating controls (a clean `n: 20` beside a refused `n: 19`,
a non-attribute axis name, an unambiguous roster beside the ambiguous one) are real discriminators
rather than fixtures that agree with the bug. The batch report's own crash-versus-assertion reading
of task 9's mutation is accurate, and I confirmed it independently.

---

## Findings

### Major 1 — a group-axis `shuffle` under a declared `cluster_by` derives its level from an attribute no unit carries, and the ambiguity refusal fails open

`src/publishable/validate.py:6297` (the `roster is not None and … shuffle in (declared | axes)`
guard) calling `src/publishable/units.py:2546` `null_test_level`, whose docstring's domain is
*"`shuffle` names an attribute"*. Task 7 widened the legal `shuffle` set to
`data.units.attributes ∪ sweep.groups` axis names — the batch's own "load-bearing half" — and task 9
then derives the level with `unit.attributes.get(shuffle)`. An axis name is not a roster attribute,
so every unit renders `no value`, every cluster is constant, and the answer is `whole_cluster`.

**Verified by running**, two ways.

1. Direct call: `null_test_level(roster, "match_set", "arm")` → `('whole_cluster', None)` on a roster
   where `arm` is carried by nobody, while `null_test_level(roster, "match_set", "label")` on the
   same roster → `('ambiguous', ('M07', 'M12'))`.
2. End-to-end through `validate_config`, on a config whose `arm` axis is
   `assign: {arm: {method: by_attribute, from: label}}` with `cluster_by: match_set` and a roster
   where `label` varies inside `M07` and is constant inside `M12` — i.e. the axis membership itself
   is ambiguous:
   - `shuffle: arm` → `['E-STATS-NULLTEST-UNSUPPORTED']`. **No assign refusal fires, and no
     `E-STATS-NULLTEST-LEVEL`.**
   - `shuffle: label`, same roster → `['E-STATS-NULLTEST-LEVEL', 'E-STATS-NULLTEST-UNSUPPORTED']`.

The composition is not refused elsewhere: `validate.py`'s own `_check_assign` comment (around the
`_read_axis_column` reasoning) states that a `by_attribute` axis whose `from` varies within a cluster
is reachable and that the consequence "was measurable rather than theoretical" — it is refused only
where such an axis is used as a later axis's *stratum*, which this config does not do.

Why it is invisible today: `test_a_shuffle_naming_a_group_axis_is_accepted` declares no `cluster_by`,
so it lands in `("rows", None)` and never reaches the level branch. **No test in the suite combines a
group-axis `shuffle` with a declared `cluster_by`** — verified by reading every new test and by the
probe above.

This is CLAUDE.md § Answering a question with a proxy almost verbatim: the `no value` convention
silently converts *this is an axis name* into *every unit is missing this attribute*, and the
predicate fails open on exactly the shape the union exists to admit. The validate-time cost is one
missed refusal; the larger cost is that `null_test_level` is minted here **for task 13 to consume**
as the chooser of the permutation construction, so a group-axis null over clustered units would be
built at the wrong level with nothing saying so.

Minimum remedy: file it in `docs/superpowers/spec-defects.md` with **owner task 13**, and state in
`null_test_level`'s docstring that its domain is a roster attribute — the call site currently passes
values outside it. Better remedy: read a group-axis `shuffle` through the axis's realized membership
the way `_read_axis_column` already does for a stratum, or refuse the axis-plus-`cluster_by`
combination.

### Major 2 — `shuffle` is not required, so a `null_test` that relabels nothing validates clean

`src/publishable/validate.py` `_check_null_test`: every `shuffle` guard is
`isinstance(shuffle, str)` (and, for `-SHUFFLE`, `and shuffle`), so `null_test.get("shuffle") is
None` silently skips `E-STATS-NULLTEST-SHUFFLE`, `E-STATS-NULLTEST-REPORTBY` and the level
derivation alike. There is no presence check anywhere in the function.

**Verified by running**, with a declared, resolvable roster carrying two attributes:

- `{"method": "permutation", "n": 5000}` (no `shuffle` key) → `['E-STATS-NULLTEST-UNSUPPORTED']`
- `{"method": "permutation", "n": 5000, "shuffle": ""}` → `['E-STATS-NULLTEST-UNSUPPORTED']`

So once task 25 retires the wholesale refusal, both validate **clean** — a declaration that permutes
nothing and changes no behavior, which is the same class of hole task 8 closed one field over for
the missing roster.

`docs/reference.md:253`, § Validation's *Null test coherence*, already states the rule:
*"`statistics.null_test` requires `shuffle` to name a unit attribute."* This is CLAUDE.md's
*assuming a documented rule has code behind it* row read from the other end — the row exists, the
check does not. **Unowned**: greps over `plans/2026-08-18-null-test.md` and the design spec for a
task requiring `shuffle`'s presence return nothing, and task 28 step 1 only *restates* that row's
condition to name the `sweep.groups` union and the `method`/`n` faults — it adds no check. Task 7
owns `_check_null_test` against that row and built the "names a unit attribute" half without the
"requires" half.

I report the two cases together but they need not resolve together: an absent `shuffle` is the
block's missing subject, while `shuffle: ""` has the `stratify_by: ""` precedent
(`reference.md` § Errors, `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`'s row) for accepting an empty name —
though that precedent is about an optional refinement, not about the field the whole block is
declared for.

### Minor 1 — the rewritten `envelope.py` comment garbles the predicate it inherited

`src/publishable/envelope.py:41-43`: *"their fixed keys (`method`, `n`, `stratify_by` for `resample`;
`method`, `n`, `shuffle` for `null_test`) **are fixed**"*. The pre-edit sentence read "its three keys
(…) are fixed"; pluralising it for two blocks moved "fixed" into the subject and left the predicate
saying nothing. Verified by reading the diff's before/after. Same sentence pair says *"both are
closed before their own wholesale refusal **retired**"* — past tense, true of `resample` and not yet
of `null_test`, repaired only by the parenthetical that follows. The batch report claims the whole
comment was re-read after editing; this is what a re-read is for. Prefer deleting the redundant
clause to rewriting it.

### Minor 2 — five emittable codes have no § Errors row on the branch today

`E-STATS-NULLTEST-METHOD`, `-N`, `-SHUFFLE`, `-UNITS`, `-LEVEL` are all emitted by
`_check_null_test` at HEAD and none has a row in `docs/reference.md` § Errors `validate` reports
(verified by grep: 0 hits each; `-REPORTBY` has exactly 1, at line 572). **Correctly attributed, not
this batch's defect**: `plans/2026-08-18-null-test.md` task 28 step 2 owns *"mint a § Errors row per
new code"*. Recorded here only so the whole-branch reviewer holds it: CLAUDE.md's one-row-per-code
invariant is unsatisfied on the branch and must land before merge.

### Minor 3 — a self-referential cross-link

The new limitation paragraph (`docs/reference.md:2893`) opens with
`[statistics.report_by](#reporting-strata)` while sitting inside `#### Reporting strata` (heading at
line 2864). Harmless; the anchor resolves. Section placement itself is correct — Reporting strata
nests under `### Statistical reporting` (line 2454), so both the brief's "§ Statistical reporting"
and the `spec-defects.md` citation of that section hold as parent references.

---

## The six attack points, each answered

**1. Five faults, five distinct code sets — CONFIRMED, verified by running.** Direct-call probe
through `validate_config` (temporary probe file, since deleted). Exact sets:

| Fault | Exact set returned |
|---|---|
| `shufle` typo | `E-CONFIG-KEY-UNKNOWN`, `E-STATS-NULLTEST-UNSUPPORTED`, `W-DATA-CLUSTER-UNDECLARED` |
| `method: bootsrap` | `E-STATS-NULLTEST-METHOD`, `E-STATS-NULLTEST-UNSUPPORTED`, `W-DATA-CLUSTER-UNDECLARED` |
| `shuffle: nope_not_an_attr` | `E-STATS-NULLTEST-SHUFFLE`, `E-STATS-NULLTEST-UNSUPPORTED`, `W-DATA-CLUSTER-UNDECLARED` |
| `n: 19` | `E-STATS-NULLTEST-N`, `E-STATS-NULLTEST-UNSUPPORTED`, `W-DATA-CLUSTER-UNDECLARED` |
| rosterless | `E-STATS-NULLTEST-UNITS`, `E-STATS-NULLTEST-SHUFFLE`, `E-STATS-NULLTEST-UNSUPPORTED` |
| `report_by` overlap | `E-STATS-NULLTEST-REPORTBY`, `E-STATS-NULLTEST-UNSUPPORTED` |
| clean baseline | `E-STATS-NULLTEST-UNSUPPORTED`, `W-DATA-CLUSTER-UNDECLARED` |

No two collapse. `E-STATS-NULLTEST-UNSUPPORTED` is present in every one of them, so every assertion
in the new tests is genuinely *alongside* it and none could pass on a total-set reading. The
rosterless case carrying `-SHUFFLE` beside `-UNITS` is **not** a finding: I probed the twin
`_check_resample` states it matches and it behaves identically — a no-units `resample` with a
`stratify_by` returns `E-STATS-RESAMPLE-UNITS` **and** `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`.

**2. The blindness claim — I tried to overturn it and could not; it HOLDS at HEAD.** Verified by
running: deleting `"statistics.null_test.shuffle": str` from `LEAF_TYPES` against the full suite at
HEAD fails **exactly one test**, and only the case the implementer added
(`test_a_wrong_typed_null_test_child_is_reported_by_the_envelope`'s `{"shuffle": 5}` half:
`assert "E-CONFIG-TYPE" in {'E-CONFIG-KEY-UNKNOWN', 'E-STATS-NULLTEST-UNITS',
'E-STATS-NULLTEST-UNSUPPORTED'}`). The mechanism, which the report does not state and which is worth
carrying: the tasks 7–9 tests **do** supply a valid `shuffle`, so the mutation makes each of them
also earn `E-CONFIG-KEY-UNKNOWN` — but they assert membership rather than exact sets, and
`_check_null_test` reads `null_test.get("shuffle")` independently of the envelope, so every
downstream check still fires and every assertion still passes. This blindness therefore did **not**
expire the way a preceding slice's did.

**The added fixture is the right remedy, not scope creep.** Task 6's brief step 5 prescribes it by
name — *"The discriminating fixture is the one that would: add `{"shuffle": 5}` … then re-apply the
mutation and confirm THAT case fails. Revert by editing the entry back"* — where "the entry" is
unambiguously the `LEAF_TYPES` entry. The implementer flagged this as a judgement call; it resolves
as a correct instruction-follow, and given the result above it is the **sole** pin on that leaf.

**3. Task 6's trap — VERIFIED by running.** `{"statistics": {"null_test": 5}}` returns
`['E-CONFIG-TYPE', 'E-STATS-NULLTEST-UNSUPPORTED']`. `"statistics.null_test": dict` is retained in
`LEAF_TYPES` (line 158) beside its three children, matching `statistics.resample`'s shape, and
`test_a_scalar_null_test_block_is_still_a_type_fault` pins it.

**4. Tasks 5 and 24 are disjoint — verified by reading both texts.** The § Errors row
(`reference.md:572`) is scoped to *which attribute is permuted*; the limitation paragraph (line 2893)
is scoped to *which construction a level's interval uses*, and carries the disjointness clause inside
itself — *"neither makes any part of the other unreachable"* — exactly as the brief required. Neither
claims the other's territory. They land in one commit (`5473585`), so the boundary is visible in one
diff. The `spec-defects.md` conversion (line ~5654) correctly restricts itself to Finding 2 and
explicitly leaves `W-STATS-REPORTBY-THIN`'s whole-roster half where § What isn't a repeat already
records it; it also states **"The code is unchanged"**, which is what stops the entry being misread
as a fix. **The limitation's factual claim is true — verified by reading `cli.py`:** the condition's
`summarize_step` call passes `resample_columns=resample_spec["declared"]` and the `report_by` level's
call (about 300 lines below it) passes no such argument, so a level's recorded column really does get
a `t_over_units` interval and no `resample` echo. **Task 5 step 5's cross-document sweep, re-run by
me:** `grep -rn 'resample_columns'` over the four documents → **zero hits** (it is an internal
`cli.py` name, so no document contradicts it and none needs repair), and `grep -n 'report_by'` over
`reference.md` filtered to sentences about intervals returns only the new paragraph itself. The file
list was filtered; no output was. Task 24's claim is now verified by sweep rather than by reading. The § Errors row states a standing reason and no *"until the construction exists"* wording,
so it reads as a permanent narrow refusal rather than a build-family deferral.

**5. The three-state answer is real, and pinned — with one qualification the report already made.**
Verified by direct call on all four states: within-cluster (varies in every cluster), whole-cluster
(constant in every cluster, unequal cluster sizes), ambiguous (`M07`/`M12`, returning both
witnesses), and `rows` (no `cluster_by`). `stratum_varies_within_cluster` genuinely cannot supply it
— it returns first-offender-or-`None` — so § Corrections' correction 4 is right that a second
function was needed. **What each state drives:** only `ambiguous` has a consumer at validate time
(`E-STATS-NULLTEST-LEVEL`); `rows`, `within_cluster` and `whole_cluster` drive nothing until task 13.
The batch report discloses exactly that, which is the honest form.

**The crash-versus-assertion reading is CONFIRMED, verified by running.** Mutating
`if varying and constant:` → `if varying and not constant:` fails four tests. The two the brief names
fail on real assertions —
`test_the_null_test_level_is_ambiguous_when_some_clusters_vary_and_others_do_not`
(`AssertionError: ('within_cluster', None) == ('ambiguous', ('M07','M12'))`) and
`test_an_ambiguous_shuffle_level_is_refused`
(`AssertionError: 'E-STATS-NULLTEST-LEVEL' in {'E-STATS-NULLTEST-UNSUPPORTED'}`). The other two are
`IndexError: list index out of range` at `units.py:2599` (`constant[0]` on an empty list). The pin is
therefore real and does not rest on a crash.

**6. The task 7 docstring trim — verified by running `git show 4fcc89f`.** The shipped mid-slice
docstring enumerates **three** checks, says outright *"this docstring names only what this function
currently does, not what the finished check will"*, names the three that tasks 8 and 9 will add, and
records that `roster` is accepted-and-unused ahead of task 9. The new scope is true, and it narrowed
away nothing the code provides — the load-bearing union clause and the leaf-type/`isinstance`
contract are both retained. At HEAD the docstring is back to the full six, and I checked each claim
against the body: six codes emitted, exactly one (`E-STATS-NULLTEST-LEVEL`) reads `roster` and
carries its own `roster is not None` guard, and every value read is `isinstance`-guarded (including
the explicit `bool` exclusion on `n`). This is the good instinct the attack list expected, executed
correctly.

**7. Four prescribed mutations re-run by me** against the full unfiltered suite, each checked against
the body of the test it named:

| Mutation | Result |
|---|---|
| Task 7 step 6: `shuffle not in (declared \| axes)` → `not in declared` | 1 failed / 2296 passed — `test_a_shuffle_naming_a_group_axis_is_accepted`, real assertion |
| Task 8 step 6: `return` after the `-UNITS` call | 1 failed / 2296 — `test_a_null_test_with_no_units_is_refused_and_the_shape_faults_still_report`, on the `-N` assertion |
| Task 9 step 6(a): `varying and constant` → `varying and not constant` | 4 failed / 2293 — two assertions, two `IndexError`s (above) |
| Task 6 step 5: delete the `shuffle` leaf entry | 1 failed / 2296 — the added discriminating case only (above) |

**8. Prose.** Mechanical pass run as a script over `reference.md`, `spec-defects.md`, the other three
documents and `CLAUDE.md`: no trailing whitespace, no tabs, no invisible unicode, no duplicate
anchors, every table row matching its header's column count, every `#anchor` resolving (the five
apparent misses were my slugger stripping `_`, confirmed by hand against `derive_seed` and
`reuse_from`). Both new rows sit in correct alphabetical position — `E-STATS-NULLTEST-REPORTBY`
between `-CORRECTION-UNKNOWN` and `-REPORTBY-UNKNOWN`, and the § Validation row beside the two
existing `null_test` rows. **Rows the insertions moved, checked:** the § The one config file
paragraph's *"four optional `statistics` sub-blocks"* still counts four; its *"One declaration above
is not yet built"* and its `-UNSUPPORTED`-is-absent-from-the-registry claim both still hold. The
whole-leaf enumeration in the unknown-key paragraph (`reference.md:~344`) does **not** list
`statistics.null_test`, so closing the block did not falsify it. No counts, positional locators or
call-site enumerations in the new prose. No undated build fact added; both `spec-defects.md`
paragraphs carry 2026-08-18 and name their task. No `×`/`x` issue (no multiplication added).
`min_honest_permutations` matches § Statistical reporting exactly — strict `1/(n+1) < level`,
`⌊1/level⌋`, 20 at α = 0.05 — and I confirmed the boundary by running (`n: 19` refused, `n: 20`
clean, which also separates it from `min_honest_draws`' 80).

**9. `E-STATS-NULLTEST-UNSUPPORTED` is alive**, absent from `reference.md` entirely (0 hits — the
`-UNSUPPORTED` family is deliberately outside the validate-time registry, as § The one config file
states), and present in every probed fault set. Every new test asserts membership alongside it, never
a total code set. **No sentence in the batch claims a config is unblocked**: `git diff 69424f4..HEAD
-- docs/ | grep '^+'` for `unblock|executable|executes|no remaining core-side` → zero hits. The
counts (zero, six, three) are untouched and unmentioned.

## What I could not check

- **Whether Major 1's wrong level actually mis-builds a permutation.** Task 13 is unbuilt, so the
  consequence is currently latent; I verified the wrong answer and the missing refusal, not a wrong
  p-value.
- **`W-DATA-CLUSTER-UNDECLARED` disappears once `statistics.report_by` is declared** on an otherwise
  identical config. Noticed in passing during the probe, almost certainly pre-existing and unrelated
  to this batch; I did not trace its emit site.
- The five § Errors rows owed by task 28 are read as owned, not verified as written — task 28 has not
  run.
