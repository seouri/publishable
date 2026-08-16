## Task 14: `allocation.json` records the draw; the refusal retires

**Files:** Modify `src/publishable/artifacts.py`, `src/publishable/validate.py`, `docs/reference.md`, `docs/experimental-designs.md`; Test `tests/test_artifacts.py`, `tests/test_cli.py`, `tests/test_validate.py`

**Only now, after everything the refusal masks is built.** H3c-1's ordering lesson: a retirement ahead of its preconditions ships a wrong number, and each of the three retirements this project has done made a latent defect live.

- [ ] **Step 1: `allocation.json` gains `seed` and `strata`.** § `allocation.json` prints them keyed by axis. **The change is *add per-axis entries for drawn axes*, not *replace the empties*** — that section says a `by_attribute` axis "is left out of both". Two tests lock the current shape literally (`doc["strata"] == {}` in `tests/test_artifacts.py`, `alloc["strata"] == {}` in `tests/test_cli.py`) and `build_allocation_document`'s four-paragraph docstring argues for the empties. All three change.
- [ ] **Step 2: The mixed case is the test that matters** — one `by_attribute` axis beside one `random` axis, asserting the drawn axis appears in `seed` and `strata` and the read one does not, in the same document.
- [ ] **Step 3: Retire `E-DATA-ASSIGN-DRAWN`.** Remove the `elif` branch and `DRAWN_ASSIGN_METHODS`. **Work from task 1's site list**, and check off each of the ten prose surfaces.
- [ ] **Step 4: Grep both directions, and prove the grep can fail.** The three retired-code greps in H3c-1 found a true hit only because the sweep was re-run without a filter — **filter the file list, never the output.** Run against a code you know is present and show the non-empty result first.
- [ ] **Step 5: Re-record the `resume` gap.** § Resuming says `allocation.json` is "read rather than re-drawn on resume". **There is still no `resume` command** — `OPERATION_COMMANDS = {"validate", "run"}` — and under `by_attribute` that was harmless because re-reading a column is idempotent. **Under a draw it stops being harmless.** Say that in `reference.md`; do not build `resume`.
- [ ] **Step 6: The `NOT BUILT` register.** Check whether retiring this code changes it — the register marks *declarations*, and this is a *method value*, so most likely it does not. **Check rather than assume**, and check the spelled count and the enumeration, not only the markers.
- [ ] **Step 7: Commit.**

---

## Sequencing

1 → 14 in order. Tasks 1–3 are the documents and two of them are **rulings**, which must land before the code that implements them. Task 4 closes the block so tasks 5–13's four new keys cannot be silently misspelled. Task 5 ships a live-gap fix that needs no drawing. Task 6 is the seed and task 7 the authority seam — **7 is the one whose failure mode is a second membership producer**, and 8–13 all consume it. Task 14 retires last, after everything the refusal masks is built.

## Where this slice will be attacked

The acceptance property, stated so task 14 can verify it: **a drawn assignment is a partition of the roster into the declared levels, reproducible from `(digest, axis, roster, seed)` alone, recorded in `allocation.json`, and identical between the plan `validate` computes and the one the runner executes.** H3c-1's bar was defeated three times — twice by a shape nobody had tried and once by the documented feature itself. Expect the same here, and expect the successful attack to come from roster content rather than config shape.
