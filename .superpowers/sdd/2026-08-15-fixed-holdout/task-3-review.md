# Task 3 review: close `data.units.holdout` one level in

**Reviewed:** `ecaa7dc..0c1f9b1` (feature commit `93372ce`). Tree verified clean at `0c1f9b1`
apart from the reviewer-owned `progress.md` edit.

**Spec compliance: ✅**
**Task quality: approved with findings** — one Important, three Minor. Nothing blocks tasks 4–7.

---

## Spec compliance

The five closed keys are exactly `method`, `frac`, `from`, `seed`, `stratify_by`, which is
exactly the set `reference.md` § Errors gives a code each (`E-DATA-HOLDOUT-METHOD`, `-FRAC`,
`-FROM`, `-SEED`, `-STRATIFY-UNKNOWN`, rows at 477–485). There is no sixth documented child, so
the closure cannot refuse a legal config. The spec's slice list item 2 — "Envelope closure one
level in; rewrite `envelope.py`'s two holdout-stays-whole comments" — is satisfied, and
over-satisfied at the comment half (see **(c)** below).

Nothing in the diff implies a declared `holdout` works. The new module comment says
`E-DATA-HOLDOUT-UNSUPPORTED` "still refuses the block **at this commit**", which is the dated
form the repo asks for.

## Behaviour verified

All by direct execution against `check_envelope` / `validate_config`, `__pycache__` cleared
between runs, every mutation reverted by editing in place.

| Check | Result |
|---|---|
| `holdout: 5` / `"random"` / `[]` / `True` | exactly **one** `E-CONFIG-TYPE` at `data.units.holdout`, no second finding, no traceback |
| `holdout: {}` | no finding — a well-typed empty `dict`, as the brief expects |
| `holdout: null` | no finding — matches `check_envelope`'s documented "a `null` is treated as absent", and matches `measurements: null` / `resample: null` |
| `methodd` / `fracc` / `stratifyy_by` | `E-CONFIG-KEY-UNKNOWN` at the exact offending path, each with the difflib suggestion naming the right key |
| `stratify_by: "label"` **and** `["label"]` | both accepted; `7` refused. The envelope and `units.stratum_names` agree on one declaration |
| `frac: "half"`, `seed: 1.5`, `seed: true` | all caught as `E-CONFIG-TYPE` here, not passed through to task 5 |
| typo + wrong-typed leaf together | both reported (`frac` type fault **and** `methodd` unknown key), so the two layers do not mask each other |

Full suite **1820 passed, 2 xfailed**; `ruff check` clean; `mypy` clean on 42 files.
`ruff format --check`: `tests/test_envelope.py` formats clean; `envelope.py` and
`tests/test_validate.py` are unformatted **pre-existing** — confirmed by running the same check
against the `ecaa7dc` copies of both files and seeing identical output, and the new hunks appear
in neither format diff. The report's account of this is accurate.

## Mutation results — every new assertion has a mutation that kills it

| Mutation | Killed |
|---|---|
| `frac` → `(int, float, str)` | `{"frac": "0.2"}` row fails ✅ |
| `stratify_by` → `list` alone | bare-string row (`block8`) fails ✅ — the dual typing is genuinely pinned, not incidental |
| `seed` → `int` alone | `seed: "auto"` row (`block11`) fails ✅ |
| delete the `frac` entry | `test_a_misspelled_holdout_child_is_reported`'s **positive companion** fails ✅ — the absence half is not absence-only |
| drop `E-CONFIG-KEY-UNKNOWN` at `validate.py:456` (wiring only) | `test_envelope.py` **all 32 green**; the new `test_validate.py` pin **fails** ✅ |

The last one is the point: the added end-to-end test is real and discriminating. It catches a
break that every test in the brief's own file scope is blind to. The out-of-scope addition was
correct and should be kept.

## The three reported brief defects — all three confirmed

**(a) confirmed, and the implementer's correction is the right one.** Setting the entry to bare
`float` leaves all 15 parametrized rows green, because `_is_type` already promotes `int` when
`float` is allowed. The brief's "typing it `(int, float)` would let `frac: 1` reach the range
check" is backwards; the tuple is documentation, not mechanism. Keeping the tuple and rewording
the comment was the right call. But see **Finding 1** — the replacement comment introduced a
different false claim.

**(b) confirmed by behaviour, and it is the important one.** Deleting only
`"data.units.holdout.method": str,` leaves `test_a_misspelled_holdout_child_is_reported`
**passing** (only a `test_each_holdout_child_is_typed` row fails, which is not what the brief
claimed to prove). Deleting all five entries makes the closure test **fail**, exactly as the
brief's reasoning describes. The brief's mutation is blind and the replacement bites. This is the
third non-discriminating mutation across two slices, and the implementer's generalization is
correct: "delete one child of N>1" can never falsify a container-derivation claim, because
`_known_containers` derives from *any* path beneath the prefix. Any future brief closing a block
with fixed children must delete **all** the entries.

**(c) confirmed, and I re-swept independently at full scope** — over `src/`, `tests/`, and the
four documents, filtering the *file list* and never the output, for `stays whole` / `left whole` /
`whole leaf` / `reached by no check` / `reported by no check` / `unreachable by any check` /
`no check in this build` / `silently ignored` / `half-closed`. The third instance the implementer
found (`_check_unknown_keys`'s docstring) is real and is correctly rewritten. No fourth instance
survives in `src/` or `tests/`. One survives in `docs/reference.md` — see **Finding 3**, which is
owned elsewhere.

## The alongside-not-instead rule

Holds. The one new `validate`-level test asserts `E-DATA-HOLDOUT-UNSUPPORTED` on its own line
*and* the `E-CONFIG-KEY-UNKNOWN` path, so task 18 deletes a line and keeps a live assertion. The
`test_envelope.py` tests call `check_envelope` directly, where that code does not exist and the
rule does not apply; task 18 does not touch them. No test pins the list without the code or only
the code.

---

## Findings

### Important

**1. The rewritten `frac` comment introduces a false sibling citation.** `envelope.py:99` now
reads "`(int, float)`, **matching `limits.max_failed_fraction`'s entry**". That entry is
`envelope.py:153`, `"limits.max_failed_fraction": float` — a bare `float`, not a tuple. The
comment cites as precedent an entry that is spelled the opposite way, and the sentence's whole job
is to justify a spelling choice, so the reader it is written for (tasks 4–7, and the next block
that gets closed) is pointed at a sibling that argues against it. This is the
comment-claiming-a-guarantee-the-code-does-not-provide class, arrived at by the specific route
CLAUDE.md names: a false claim introduced inside a commit whose stated purpose was fixing a false
claim. Fix by citing `statistics.resample.n`'s spelling if it is a tuple, or by dropping the
citation and keeping only the `_is_type`-promotion sentence, which *is* verified true.

The other two citations in the new comments check out and are worth recording as verified:
`statistics.resample.stratify_by` really is `(str, list)` (`envelope.py:143`), and
`### What auto derives from` really is a heading in `reference.md` (line 2734).

### Minor

**2. The report overstates task 18's cleanup here.** It says the new `test_validate.py` pin makes
task 18 "a one-line deletion here too, same as the `test_envelope.py` tests". Deleting the
assertion is one line, but the test is *named*
`test_a_misspelled_holdout_child_is_reported_alongside_the_wholesale_refusal` and its docstring is
three sentences about that refusal — so task 18 also owes a rename and a docstring rewrite, or the
suite carries a test whose name asserts a relationship no assertion makes. That is the exact
name-claims-the-guarantee shape from CLAUDE.md. Not a code defect; a report claim to correct so
task 18 is not surprised. (Task 18's half-one instruction is a `grep`, not a count, so the sixth
pin is discovered rather than missed — no count phrase went stale.)

**3. `docs/reference.md:456` now states the opposite of the code, and its owner will only close
half of it.** The `E-CONFIG-KEY-UNKNOWN` row still says "a typo inside `data.units.holdout` or a
`from` mapping is reached by no check at all ... and `holdout` is not among them only because the
whole block is refused today". Both halves are now false. This is **owned** — plan task 19 step 3
item (e) names it, and step 2's sweep string matches the line — so it is not task 3's to fix, and
the normative-doc lag is planned rather than silent. But item (e) as drafted replaces only the
trailing parenthetical ("and `holdout` is not among them only because..."); it leaves the earlier
clause "a typo inside `data.units.holdout` or a `from` mapping is reached by no check at all"
untouched and false. Flagging so task 19 fixes the whole row rather than the string its brief
quotes. `reference.md:188`'s "`.holdout` inherits the same treatment when its slice lands" is
still fair — the slice has not landed — and needs no change now.

**4. The rewritten module comment leaves ragged wrapping.** Two paragraphs now carry short orphan
lines mid-flow (`# check already approved. The optional blocks that`, `# its children's names
being fixed. The keys that`) because the replacement text was dropped in at the brief's exact
line breaks. Cosmetic, brief-mandated, and reflowing it is a one-minute edit whoever next touches
this docstring can absorb.

## Not findings, recorded so they are not re-derived

- `holdout: null` producing no finding is correct and consistent with the two sibling blocks; the
  brief did not name it and the behaviour needed checking.
- `seed: "x"` is accepted by the envelope. That is intended — `(str, int)` admits any string so
  that `auto` passes, and refusing a non-`auto` string is `E-DATA-HOLDOUT-SEED`'s job in task 5.
  The division of labour matches `reference.md:481`.
- No closed key set of the implementer's own was introduced; the closure falls out of
  `_known_containers`' derivation from `LEAF_TYPES`, which is the precedent's mechanism exactly.
