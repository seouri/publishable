# Task 12 review: `units.holdout_seed_for`

Reviewed 2026-08-16 against `e3ed9a1..605f63c` (single commit `605f63c`).

## Verdicts

1. **Spec compliance: ✅** — the function is the brief verbatim; its pin gate is character-identical
   to the one `validate` enforces for `E-DATA-HOLDOUT-SEED`; the digest it mixes is the one
   `hashes._units_excluding_drawn_seeds` strips `holdout.seed` from, so the derivation is not
   self-referential; its payload is distinct from every other digest-derived seed in `src/`; the
   4-byte big-endian truncation matches all four sibling 4-byte derivations and is pinned by an
   assertion.
2. **Task quality: ✅ with one Important finding** — every added test is reached by a single-line
   mutation (I ran three of my own beyond the report's five, including one the report's mutation (b)
   could not reach), and the implementer's negative finding about mutation (e) is **verified true**.
   The one defect is a new docstring sentence that over-claims and is falsified by a sibling the
   same docstring names two paragraphs above.

---

## Spec compliance — what I checked, and how

### 1. Parity with `E-DATA-HOLDOUT-SEED` (`validate._check_holdout`), on every shape

`validate.py:2835-2846` reads:

```python
if "seed" in holdout:
    seed = holdout["seed"]
    pinned = isinstance(seed, int) and not isinstance(seed, bool)
    if not pinned and seed != "auto":
        c.error("E-DATA-HOLDOUT-SEED", ...)
```

`units.holdout_seed_for` uses the same predicate, `isinstance(seed, int) and not isinstance(seed, bool)`.
Shape-by-shape (read from both sources, not inferred):

| `seed` | `validate` | `holdout_seed_for` | Agree? |
|---|---|---|---|
| absent | accepted (key absent) | derives (`block.get("seed", "auto")`) | yes |
| `"auto"` | accepted | derives | yes |
| `1234` / `0` / `-5` / `10**30` | accepted (plain `int`) | returned literally | yes |
| `True` / `False` | refused | derives (not honoured as `1`/`0`) | yes — refused upstream, and the runtime fallback is the safe one |
| `"1234"` | refused | derives | yes, same |
| `1.0` / `1.5` | refused | derives | yes, same |
| `None` (`seed: null`) | refused (`in` is true, not pinned, `!= "auto"`) | derives | yes, same |

No shape exists where one accepts and the other rejects. The three shapes `validate` refuses all fall
to the derivation rather than to a silent pin, which is the fail-safe direction.

**A pinned value validate admits cannot crash the consumer.** `holdout_for` seeds with
`random.Random(seed)` (`units.py`, inside `holdout_for`'s unclustered branch), which accepts negative
and arbitrarily large integers — unlike `numpy.random.default_rng`, which rejects negatives. **Verified
by grep for `Random(`/`default_rng` across `holdout_for`'s body**: one `random.Random(seed)`, no numpy
generator. Not a finding; recorded because "validate accepts a negative pin" is only safe if the
consumer does.

### 2. The digest it consumes excludes `holdout.seed` (task 4)

`hashes._units_excluding_drawn_seeds` drops `holdout["seed"]` before `design_digest` canonicalizes
`data.units` (`hashes.py:115-118`), and `design_digest` routes `data.units` through it
(`hashes.py:128`). `holdout_seed_for` takes the digest as a parameter — it does not compute one — so
the self-referential fault § What `auto` derives from names cannot arise **provided the composing call
site passes `design_digest(doc)`**. That composition is task 13 (plan line 2372: "task 13 composes the
two in `cli.command_run`"); at this commit `holdout_seed_for` has **no production caller** (verified:
`grep -rn "holdout_seed_for" src/ tests/` returns only the definition and the new tests). Nothing for
this task to fix; noted so task 13's reviewer checks the digest actually handed over.

### 3. Suffix distinctness against **every** sibling, not just the two tested

Unfiltered sweep, `grep -rn "int.from_bytes" src/` plus a call-site sweep for each helper. Every
digest-derived seed in `src/`, with its full payload:

| Derivation | Payload | Bytes |
|---|---|---|
| `units._seed_from` (fold partitions) | `{digest}\|folds` | 4 |
| `units.assign_seed_for` | `{digest}\|assign\|{axis}\|{units_hash(roster)}` | 4 |
| `units.holdout_seed_for` **(new)** | `{digest}\|holdout\|{units_hash(roster)}` | 4 |
| `replication._seed_for` (repeat seeds) | `{digest}\|{kind}\|seed\|{index}` (via `_seed_for(f"{digest}\|{kind}", i)`) | 4 |
| `replication.order_seed_for` | `{digest}\|order\|seed\|0` | 4 |
| `sweep._sample_seed` | `{digest}\|sample\|{index}` | 4 |
| `stats.resample_seed` | `{digest}\|resample` | 4 |
| `base_step.derive_seed` | `{digest}\|{execution seed}\|{purpose}` | 8 |

The holdout payload's second pipe-delimited field is the literal `holdout`; no other derivation's
second field can take that value — `folds`, `assign`, `sample`, `resample`, `order`/`{kind}` are all
literals or come from the closed repeat-kind set (`seed`, `fold`, `batch`), and `derive_seed`'s second
field is an integer seed. **The "term that can itself be empty" shape does not bite here**: the
degenerate `assign` case (`axis == ""`) renders `{digest}|assign||{hash}`, which still differs in field
2. The digest itself is `sha256:<hex>` and carries no pipe. No collision is reachable.

### 4. The truncation

`digest()[:4], "big"` — identical to all five 4-byte siblings; only `base_step.derive_seed` takes 8,
and it is documented as a different thing. Nothing in the new docstring or tests claims more than 32
bits of entropy; the range is pinned by `assert 0 <= base < 2**32`. **Verified by mutation**: changing
`[:4]` to `[:8]` fails `test_the_derived_holdout_seed_mixes_the_digest_and_the_resolved_roster` at that
assertion (run, then reverted by copying a pre-mutation backup back, `diff`-clean, tests re-run green).

### 5. Docstring citations resolve

`§ What auto derives from` (reference.md:2734) carries the row `data.units.holdout.seed | digest + the
resolved roster`, which is exactly what the code mixes; `§ Where units come from` (reference.md:1175)
exists; `E-DATA-HOLDOUT-FOLD` has a real emit site (`validate.py:2925`, enumerated at `validate.py:2693`),
so the docstring's "mutually exclusive declarations at this commit" is backed by code, not by a
documented rule with nothing behind it. `E-DATA-HOLDOUT-UNSUPPORTED` is untouched by this task.

---

## Findings

### F1 (Important) — "one derivation shape for every drawn partition in the config" is false, and the same docstring falsifies it

`units.py` (`holdout_seed_for`'s third paragraph):

> The construction is otherwise copied deliberately: the same digest, the same `units_hash`, the same
> four bytes read big-endian — **one derivation shape for every drawn partition in the config.**

A **`fold` level is a drawn partition** and its seed is `_seed_from(digest)` = `sha256(f"{digest}|folds")`
— no `units_hash`, no roster term at all. `sweep.sample`'s draw is a second counterexample
(`{digest}|sample|{index}`), and `derive_seed` reads eight bytes rather than four. The falsifying
sibling is named **two paragraphs above in this very docstring**, whose whole point is that
`_seed_from`'s payload is different.

Under a loose reading ("shape" = sha256 of a pipe-joined payload, truncated big-endian) the sentence is
true, but the clause it is appended to enumerates `units_hash` as part of the shape, and folds do not
carry it. This is the repo's recurring "a comment claiming a guarantee the code does not provide", and
it is **new to task 12** — `assign_seed_for`'s docstring, which the rest of this one is copied from,
contains no such sentence (verified by reading `units.py:2568-2592`).

**Suggested repair** (one clause, no new enumeration to go stale): end the sentence at "read
big-endian", or narrow it to "the same shape every partition drawn *over the roster* uses".

**Verified by**: reading `units.py:2564-2565` (`_seed_from`), `sweep.py:282-289`, `base_step.py:48-50`,
and `units.py:2568-2592`.

### F2 (Minor) — the payload literal is not pinned; a suffix rename passes the whole suite

**Verified by mutation**: changing the payload to `f"{digest}|folds|{units_hash(roster)}"` — which
changes **every derived holdout seed in every future run** — leaves the *full* suite green
(`uv run pytest` → 1924 passed, 2 xfailed under the mutation). Reverted from a backup copy, `diff`-clean,
suite re-run.

This is not a task-12 regression: `assign_seed_for` and `sample_seed_for` are tested the same relational
way (`tests/test_units.py:237-289`, `tests/test_sweep.py:636-675`) and pin no golden value either, so
the new tests match the house standard exactly. The residual worth recording is narrower: the
fold-distinctness test is a **point comparison against today's `_seed_from`**, not a payload-shape
invariant, so it would not survive a later slice adding a roster term to `_seed_from` — the two payloads
would then differ only in the literal `folds` vs `holdout`, and any edit that made them agree would go
undetected by everything except that one comparison. Nothing to change now; the test does hold the line
it was written to hold.

### F3 (Minor) — the report's `git checkout --` on `.superpowers/sdd/.gitignore`

The report volunteers it, and the reasoning holds (the file had no uncommitted content of its own; the
clobber was `scripts/task-brief`'s and the tracked content was the correct one). But `git checkout --`
is the move CLAUDE.md names by hand as having been mistaken for a revert twice. `git restore --source=HEAD`
is the same operation with the same risk; the safe form is editing the file's content back. Recorded
because the habit, not this instance, is the hazard.

---

## Mutation coverage — every added test, with the single-line mutation that kills it

Five tests, five distinct mutations. The report ran five; I ran three more (marked ★), one of which
closes a gap the report's own text acknowledges.

| Test | Killing mutation | Result |
|---|---|---|
| `..._pinned_holdout_seed_is_returned_literally_and_ignores_the_digest` | delete the early return (report's (c)) | FAIL, as reported |
| `..._boolean_seed_is_not_a_pin` — 1st assertion | `isinstance(seed, int)` without the `bool` exclusion (brief's (b)) | FAIL, as reported |
| `..._boolean_seed_is_not_a_pin` — **2nd assertion** ★ | `payload = f"{digest}\|holdout\|{seed}\|{units_hash(roster)}"` | **FAIL at `tests/test_units.py:3633`, and only this test** — `{}` and `{"seed": "auto"}` both render `auto`, so the derived-seed test still passes, while `{"seed": True}` renders `True` |
| `..._derived_holdout_seed_mixes_the_digest_and_the_resolved_roster` | drop the roster term (report's (d)); ★ also `[:4]` → `[:8]`, which fails the `< 2**32` assertion | FAIL |
| `..._holdout_seed_is_not_the_fold_seed_for_the_same_digest` | payload → `f"{digest}\|folds"` (report's (e)) | FAIL |
| `..._holdout_seed_is_not_an_assign_axis_seed_for_the_same_digest` | payload → `\|assign\|holdout\|` (brief's (a)) | FAIL |

The ★ boolean mutation matters because the report is explicit that pytest stopped at the first
assertion under mutation (b), leaving the second assertion (`derived == holdout_seed_for({}, ...)`,
i.e. *a boolean falls through to the same value the default path derives*) reached by no mutation at
all. It is now independently discriminated.

**No test survives a constant-returning construction**: `test_the_derived_...` alone fails on three
assertions if the derivation returns a constant, and the pinned test fails if the pin is dropped.

**The implementer's negative finding is VERIFIED, and is a real property of the payload.** Their claim
is that mutation (e) cannot be isolated from (d). I re-ran their proposed narrower variant myself —
payload `f"{digest}|folds|{units_hash(roster)}"`, keeping the roster term — and the **full suite passes**
(§ F2 above), confirming it does not collide with `_seed_from` and therefore does not reach the fold
test. Since `_seed_from(digest)` mixes no roster at all, any edit making `holdout_seed_for` agree with
it on some input must drop `units_hash(roster)` from the payload, which necessarily also fails the
roster half of `test_the_derived_...`. So the fold test is not independently reachable by a one-line
mutation, and this is a property of `_seed_from`'s payload shape rather than a weakness the implementer
chose. Disclosing it rather than claiming a clean single-property proof is the right call and is the
strongest part of the report.

## Process

`uv run pytest` (green at HEAD and after every revert), `uv run ruff check .` → All checks passed,
`uv run mypy` → Success, 42 source files. All mutations were applied to `src/publishable/units.py` in
place and reverted by copying back a pre-mutation backup taken to the scratchpad — never
`git checkout --` — with `__pycache__` deleted, each revert verified by re-running the targeted tests
and by `diff` against the backup (byte-identical), not by `git status`.
