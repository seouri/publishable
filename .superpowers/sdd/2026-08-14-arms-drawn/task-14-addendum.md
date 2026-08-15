# Task 14 — controller additions

**The retirement is the irreversible half of this slice.** This project has retired a build refusal four
times and **each time the retirement made a latent defect live**. The ordering exists for that reason.

## The site list is TWELVE doc sites plus six source files, not ten

Task 1 measured it. Nine `reference.md` sites and one in `experimental-designs.md` name the code string;
**two more sentences describe the same fact without naming it** — `reference.md` § Expansion modes and
`experimental-designs.md` § Crossed group axes, both "carries the same refusal … as the single-axis
example above". A code-string grep finds ten of twelve. Task 1's report has the list; work from it.

Six source/test files also name it: `units.py`, `validate.py`, `cli.py`, `artifacts.py`, `test_cli.py`,
`test_validate.py`.

## Prove the grep can fail, and never filter its output

Filter the **file list**, never the sweep's output. In the previous slice a reviewer checking this exact
rule lost a true hit to `grep -v superpowers`, because the matching line contained that path. Run each
sweep against a code you know is present and show the non-empty result **before** trusting the empty one.

## What must be checked off before the refusal goes

- **`DRAWN_ASSIGN_METHODS` lives in `units.py`** and `validate` imports it. After the retirement
  `validate`'s use disappears while the draw's remains — check what is left of the import.
- **`assignment_for` is an allowlist**: `by_attribute`/absent/method-less read a column, everything else
  raises. Tasks 8, 10 and 12 filled `random` and `blocked`. **Confirm nothing still raises
  `NotImplementedError` for a method the enum now admits** — that raise is not a `PublishableError`, so
  it would print a traceback rather than a diagnostic.
- **`blocked` beside `cluster_by`** stays refused (task 11). The retirement must not lift it.

## The validate-clean-then-disagree gap task 8 routed here

When `E-DATA-ASSIGN-DRAWN` retires, **`ratio {a: 1, b: 1000}` over a 10-unit roster validates clean and
raises `E-DATA-ASSIGN-LEVELS` at the draw.** The closing check is roster-dependent, so it belongs beside
`E-DATA-ASSIGN-LEVELS`'s existing roster-resolved check rather than in the declaration-only `ratio`
family. **Decide: close it, or record it in `reference.md`.** Do not leave it undecided — the whole point
of retiring last is that the masked cases get handled.

## `allocation.json` gains `seed` and `strata`

**Add per-axis entries for drawn axes; do not replace the empties.** § `allocation.json` says a
`by_attribute` axis "is left out of both". **The mixed case is the test that matters** — one
`by_attribute` axis beside one `random` axis, asserting the drawn one appears in `seed` and `strata` and
the read one does not, in the same document.

Two tests lock the current shape literally (`doc["strata"] == {}` in `tests/test_artifacts.py`,
`alloc["strata"] == {}` in `tests/test_cli.py`) and `build_allocation_document`'s docstring is a
four-paragraph argument for why the keys are empty. All three change.

`artifacts.allocation_hash` hashes the **document canonically**, not the file bytes, so it covers the new
keys the moment they are populated — no hash-shape change. But **two `allocation_hash` digests are pinned
as literals** in the suite; they move only if a `by_attribute`-only document changes, which it must not.

## Re-record the `resume` gap

§ Resuming says `allocation.json` is "read rather than re-drawn on resume". **There is still no `resume`
command** — `OPERATION_COMMANDS = {"validate", "run"}`. Under `by_attribute` that was harmless because
re-reading a column is idempotent. **Under a draw it stops being harmless.** Say that in `reference.md`;
do not build `resume`.

## The `NOT BUILT` register

Check whether the retirement changes it. The register marks **declarations**, and this is a **method
value**, so most likely it does not — **check rather than assume**, and check the spelled count and the
enumeration, not only the markers.

## A pre-existing trap in § Errors core raises

`arms_of`'s run-time `E-DATA-ASSIGN-LEVELS` is absent from that table, and **that section's closing
paragraph locates a row by position ("That last row")**, so inserting one breaks it. If you add a row,
fix the phrase — name what the row does, not where it sits.

## A second latent defect routed here — from task 13, and it is the shape this addendum opens with

**An axis-name stratum never reaches `E-DATA-ASSIGN-STRATIFY-VARIES`**, whose loop appends only
declared-*attribute* strata to its resolvable set. Consequence, measured on a real fixture rather than
argued: with `cluster_by: family_id`, an earlier `by_attribute` axis whose `from` **varies within a
cluster** splits that cluster between its own arms; the halves land in different strata and are
allocated independently, so **a cluster straddles both arms — at 30 of 30 seeds in the reviewer's
fixture, 17 of 30 in the implementer's.** That contradicts § Clustered units' *"core computed the
partition, so core keeps it indivisible"*.

**Preconditions:** it needs `from` ≠ the axis name (so the constancy check on `from` does not already
refuse it), and it is **unreachable while `E-DATA-ASSIGN-DRAWN` stands** — which is exactly what this
task removes. That is why it lands here rather than being left in a report.

**Decide and act; do not leave it undecided.** Either extend the constancy check to axis-name strata —
a new rule, so it needs a § Validation row — or record the gap in `reference.md` beside § Clustered
units' indivisibility claim so a reader meets it where the promise is made. **Not `spec-defects.md`:
that file is gitignored and does not survive the merge**, which is the standing lesson of this project.
