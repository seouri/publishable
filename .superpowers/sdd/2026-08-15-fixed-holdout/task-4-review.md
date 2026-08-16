# Task 4 review: `design_digest` excludes `holdout.seed`

**Base** `cdf7295` → **HEAD** `5ff2448` (`2196a45` is the code commit).

**Spec compliance: ✅**
**Task quality: ❌** — one blocking finding (`reference.md` § What `auto` derives from now contradicts
itself), plus one Important test gap and four Minor findings.

Everything below states how it was verified. Every mutation I ran was reverted **by editing the file
back in place** and confirmed by `diff` against a pre-mutation copy plus a green re-run — never by
`git checkout --`, never by `git status`.

---

## Spec compliance — ✅

| Brief requirement | Verified |
|---|---|
| `_units_excluding_assign_seed` → `_units_excluding_drawn_seeds`, dropping `holdout.seed` too | Read `src/publishable/hashes.py` § `_units_excluding_drawn_seeds` — matches the brief's Step 3 code exactly, character for character |
| `design_digest` calls the new name | Read the call site; docstring first line widened as specified |
| Three tests appended verbatim | Read `tests/test_hashes.py`; the three tests match the brief modulo `ruff` line wrapping |
| Old name gone from `src/`, `tests/` | `grep -rn "_units_excluding_assign_seed" src/ tests/` → 0 hits (filtered the *file list*, not the output) |
| Sweep can fail | `grep -rln "_units_excluding_drawn_seeds" src/ tests/ docs/` → 3 files. Sweep is live |
| `spec-defects.md` open half struck, not deleted | Read lines 4881–4900. `~~One field over, the same defect is latent.~~ Closed by H3d, task 4.` — struck, body retained, **Found by/Closed by** now names both halves and both closers. Correct per CLAUDE.md's one-exception rule |
| The closure claim is accurate | `reference.md` § What `auto` derives from does carry the `data.units.holdout.seed` table row and names `E-DATA-HOLDOUT-SEED` (two sites: the § Errors row and the *An omitted `seed` is `auto`* paragraph). The claim is true |
| Suite / lint / types | `uv run pytest` → **1823 passed, 2 xfailed** (matches the report). `ruff check` clean, `mypy` clean over 42 files |

The strike is done well: rather than rewriting the *closed* half's history, it preserved it —
`` `hashes._units_excluding_drawn_seeds` (named `_units_excluding_assign_seed` until renamed by H3d
task 4) `` — so task 16's record still reads true at the time it was written. That is the right
handling of a live list that also functions as a record.

---

## CRITICAL — blocking

### C1. `reference.md` § What `auto` derives from now states two different answers to "what does the digest cover"

**Verified by reading, and by grep:** `grep -rn "every field except" docs/ src/ README.md CLAUDE.md`.

`docs/reference.md` § What `auto` derives from opens with:

> derives from a **design digest** over `data.units` (every field except `assign.seed` itself) and `sweep.groups`

Three paragraphs later, the same section says:

> A pinned `holdout.seed` is excluded from the design digest the same way a pinned `assign.<axis>.seed` is

Both sentences are in one normative section, and after this commit only the second is true of the
code. The tell that the divergence was seen at the code end and not at the doc end: the new
`design_digest` docstring is that opening sentence, **rewritten** — `(every field except a drawn
partition's own seed)` — while the sentence it mirrors was left alone. `hashes.py:122` and
`reference.md:2736` are now the same sentence saying two different things, with the document (which
leads) holding the false one.

**Why this is task 4's, not a later task's.** This slice already ruled on exactly this question one
task ago. `progress.md`, task 2: *"CLAUDE.md says both consistency passes run BEFORE AN EDIT IS
FINISHED, so the cross-document pass is the editing task's obligation, not a later task's"*, with the
generalization *"NEVER SHIP A DOCUMENT STATE THAT IS FALSE, IN EITHER DIRECTION."* The same
conclusion follows here. It must land **before task 5**, which is what makes a pinned `holdout.seed`
reachable at all — the same "before any pin is reachable" argument the brief uses for the code change.

**The reasoning error in the report**, worth naming because it will recur: the report says *"verified
rather than assumed: § What `auto` derives from already carries both the prose sentence and a table
row … so no doc change was owed here."* That verifies the **addition** and never checks the
**contradiction**. A section can gain a correct sentence and still hold a false one — which is the
repo's own "sweep for the claim, not the file" trap, one section wide.

**Remedy, and two guardrails so it does not overreach:**
- Edit `reference.md`'s parenthetical only — e.g. `(every field except a drawn partition's own seed —
  `assign.<axis>.seed` and `holdout.seed`)`.
- **Do not touch `spec-defects.md:4864.`** It quotes the old parenthetical as what the document said
  *when the defect was filed*; that quote is evidence and must keep reading as it did.
- **Do not touch `H3c-SCOPING.md:188`**, which quotes it for the same reason. Dated evidence.

---

## IMPORTANT

### I1. The one behavioural shape the rewrite actually widened is pinned by no test

**Verified by a mutation I ran.** The old function returned `units` untouched whenever `assign` was
not a mapping; the new one falls through to the holdout branch. That fall-through *is* the fix for
the shape the brief itself flags as "a coincidence of the current shape, not a guarantee". I restored
the old early return in a form the existing fixtures cannot see:

```python
assign = out.get("assign")
if assign is not None and not isinstance(assign, dict):
    return out          # fail-open: a pinned holdout.seed survives into the digest
if isinstance(assign, dict):
    ...
```

`uv run pytest tests/test_hashes.py` → **17 passed**. The whole file is green with the exclusion
disabled for that shape. Reverted in place; `diff` against the pre-mutation copy is empty and the 17
pass again.

No fixture carries a non-mapping `assign` **together with** a pinned `holdout.seed`: test 1 and test 3
omit `assign` entirely, test 2's is a proper mapping. This is the catalogue's *"a seam named in the
brief and instantiated by no fixture"* — the brief named the seam in Step 2's own reasoning and no
config separates the readings.

**Consequence, stated honestly:** nil today, because a config with a non-mapping `assign` is refused
before it runs. It goes live the moment anyone refactors that fall-through back toward an early
return — which is precisely the shape that existed here two commits ago.

**Remedy:** one config, three lines —
`{"assign": "nonsense", "holdout": {"method": "random", "frac": 0.2, "seed": 1}}` asserted digest-equal
to the same config without the `seed` key.

---

## MINOR

### m1. The `moved` fixture's comment claims an edit the fixture does not make

**Verified by reading `tests/test_hashes.py`, `test_the_seed_exclusion_covers_assign_and_holdout_together`.**
The comment reads *"A non-seed edit inside the SAME two blocks still moves it, so the exclusion is
per-field rather than per-block."* Diffing `moved` against `cfg(7, 11)`: the sole difference is
`assign.arm.method` `random`→`blocked`. The `holdout` block is byte-identical. The comment says two
blocks; the fixture edits one, so the holdout half of the "per-field, not per-block" claim rests on
nothing in this test. (It *is* covered — see the note under "not a finding" below — just not here.)
A one-word fix, or a second `moved` varying `holdout.frac`.

### m2. The report's sweep claim understates the sweep by ten hits

**Verified:** `grep -rn "_units_excluding_assign_seed" src/ tests/ docs/` → **12 hits across 4 files**:
`spec-defects.md` (2), `H3d-SCOPING.md` (3), `H3d-SCOPING-2.md` (2), `plans/2026-08-15-fixed-holdout.md`
(5). The report says the sweep "returns nothing in `src/`/`tests/`; the two remaining hits in
`spec-defects.md` are narrative sentences". **The action taken was right** — a scoping and a plan are
dated development record and must not be retro-edited — but the claim as written does not describe
what the command returns, and a later reader re-running it will find hits the report says are not
there. Say "the ten remaining hits are in the untouchable development record", which is both true and
the stronger statement.

### m3. A third brief defect the implementer did not surface

**Verified by the same grep.** Brief Step 4 says the sweep "must return **nothing**" over
`src/ tests/ docs/`. That is unsatisfiable: `docs/superpowers/` holds three dated records that name
the old function and may not be edited. The report surfaced two brief defects; this is a third, of the
same class as the two it did surface.

### m4. `design_digest`'s docstring says pinning "redraws nothing"

**Verified by reading `hashes.py:124-126`:** *"A parameter edit redraws nothing, and neither does
pinning or changing an axis's `assign.seed` or `data.units.holdout.seed`."* Read literally that is
false in the new half: pinning `holdout.seed` redraws **the holdout** — that is the entire purpose of
pinning it. The intended sense is "redraws nothing *else*", which is what the function's own docstring
says correctly two paragraphs up. Pre-existing wording carried one field over rather than introduced,
but the commit is what made it a claim about two seeds.

### m5. A false citation inside a verification claim — second consecutive task

**Verified:** `grep -n "ruff format" CLAUDE.md` returns exactly one hit, the command table row
(`| Format | uv run ruff format . |`). CLAUDE.md documents **no** baseline reformat count, so the
report's *"67 files … matches the pre-existing baseline CLAUDE.md records"* cites a record that does
not exist. Task 3's review recorded the identical shape one task ago (a rewritten comment citing
`limits.max_failed_fraction` as precedent for something that entry does not do); this is the second
instance in consecutive tasks, which is what makes it worth naming.

**The number itself is right, and I checked it rather than assuming.** In a scratch worktree:
`cdf7295` → `67 files would be reformatted, 266 already formatted`; `5ff2448` → `67 files would be
reformatted, 267 already formatted`. **Identical count before and after**, so the `ruff format .`
accident left no collateral in the commit, and the hand-revert of `test_hashes.py`'s pre-existing
`test_design_digest_excludes_assign_seed_with_a_control` hunk is confirmed — that file is still in the
"would be reformatted" set, exactly as it was at base. (Run this from a clean checkout; in the live
working directory the same command reports 63, a local-state artifact, not a regression.)

---

## Verified and NOT a finding

- **Mutation 1 (brief Step 5, `if False and ...`)** — I ran it: `test_a_pinned_holdout_seed_does_not_move_the_design_digest`
  and `test_the_seed_exclusion_covers_assign_and_holdout_together` both **FAIL**. Confirmed.
- **The implementer's correction to mutation 2 is right, and the brief's original was blind.** I ran
  the corrected unguarded form (`if isinstance(holdout, dict): out = {**out, "holdout": None}`) — the
  test fails on `assert design_digest(base) != design_digest(widened)`, the intended assertion. The
  brief's gated form cannot reach that assertion, because neither `base` nor `widened` carries a
  `seed` key, so the mutated branch never fires for either. The implementer's Issue 2 is confirmed
  by execution, not by argument.
- **Test 3 is not vacuous and pins the holdout shapes uniquely.** Mutation
  `if holdout is not None and "seed" in holdout:` (the narrowest fail-open that touches only the
  non-mapping path) → **exactly one failure**, `test_the_seed_exclusion_never_raises_on_a_shape_it_did_not_expect`,
  `TypeError: argument of type 'int' is not iterable`. Reverted in place; green.
- **The holdout exclusion is per-field, not per-block, and that IS pinned** — just not by the comment
  in m1. `assert design_digest(base) == design_digest(pinned)` forces the seed-stripped dict to equal
  a naturally seedless one, so any over-broad comprehension (`{}`, or one dropping `frac` too) breaks
  it. Credit the fixture; only the comment overclaims.
- **Every docstring sentence checked against the code.** *"Every other field of both blocks still
  moves the digest"* — true: the code removes the single key `"seed"` and nothing else, and
  `_canonical` is `json.dumps(sort_keys=True)` over the whole mapping, so any surviving key's change
  moves the hash. *"This function never raises"* — true for all four enumerated shapes; traced each
  branch: non-mapping `units` returns early, non-mapping `assign` and non-mapping axis block and
  non-mapping `holdout` all fail their `isinstance` and are left in place, and every `.get`/`.items()`
  call is guarded by a `dict` check. (The docstring is careful not to promise the *caller* never
  raises — `_canonical` still can, on an unserializable value. Correct as written.)
- **`units.py:2124`'s "`hashes.design_digest` strips `assign.<axis>.seed` per axis"** is not stale —
  it sits inside `assign_seed_for`'s docstring and claims only what it claims. No sweep hit owed.
- **`git checkout --` on ~67 files during the ruff accident lost nothing.** Affirmatively checked
  because CLAUDE.md names that command as having destroyed uncommitted work twice: the review
  package's `progress.md` hunk carries all of tasks 1, 2 and 3's entries intact (+135 lines), and the
  67/67 count above shows the tree matches base outside the three intended files.
- **Task 5 is genuinely still ahead of the pin.** `grep -rn "holdout_seed_for\|holdout_for" src/` →
  0 hits, so no pinned `holdout.seed` is reachable yet. The brief's ordering argument holds.

---

## Housekeeping for the controller

`git status --short` currently shows `.superpowers/sdd/.gitignore` modified — clobbered back to a bare
`*` (23 lines removed), the `sdd-workspace`/`task-brief` behaviour CLAUDE.md documents. Restore its
content and use `git add -f` for new records. Not attributable to this task's commit; noticed while
verifying the revert.
