## Task 9: `random` and `blocked` are refused as method values

**Files:** Modify `src/publishable/validate.py`; Test `tests/test_validate.py`

**Refuse the value, honour the block** — H3a's `E-DATA-WEIGHT-CONTRAST` and H3b's `E-DATA-CLUSTER-DERIVED` are the precedent. The message says what is wrong, what to do instead, and that H3c-2 lifts it.

- [ ] **Step 1–6:** Failing tests for each value plus a `by_attribute` control that must pass; implement; **mutate each value separately**; registry row; commit.

---

## Controller additions — these are requirements, same force as the brief above

**The identifier is `E-DATA-ASSIGN-DRAWN`.** Not `-UNSUPPORTED`: that suffix is this build's
*broad* family, the five-field loop that refuses a whole declaration and vanishes without a trace in
`reference.md`. This refuses a **value while honouring the block**, which is the narrow family —
`E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-DERIVED`, `E-SWEEP-SAMPLE-BASELINE` — and that family is
documented. Read `E-DATA-WEIGHT-CONTRAST`'s row in `reference.md` § Errors `validate` reports before
writing yours; it is the model for both the message and the row.

**Where it goes:** in `_check_assign` (added by tasks 7–8), which already walks the `assign` blocks.
`E-DATA-ASSIGN-METHOD` refuses a method that is *absent or out of enum*; this refuses one that is
**in the enum and not yet implemented**. They are mutually exclusive by construction — write it so
that is a property of the code, not a coincidence of ordering.

**The message must say three things** (the narrow family's contract): that drawing an arm is
specified but not implemented in this build; that `by_attribute` — reading an arm a trial system or
the data already assigned — is the supported method and is what a real trial does regardless
(`reference.md` § Allocation says exactly this); and that the value will be honoured in a later
slice. Do **not** write "H3c-2" or any internal slice name into a user-facing message — no shipped
message names one. Check the existing `-UNSUPPORTED` messages for the phrasing they use.

**Registry row:** § Errors `validate` reports is sorted. `E-DATA-ASSIGN-DRAWN` sorts **before**
`E-DATA-ASSIGN-METHOD` and `E-DATA-ASSIGN-MISSING`. There is one pre-existing sort violation in that
table (`E-SWEEP-ABLATE-BASELINE-GROUP` after `E-SWEEP-ABLATE-CROSSED`) — **leave it**, task 20 owns
it; do not let it talk you into an unsorted insertion of your own.

**Also add a row to § Allocation**, or amend what is there: that section documents `random` and
`blocked` as if they work. It must say they are refused in this build and name the code. **The
document leads the code** — if you find the section already says something incompatible, change the
document, do not weaken the check.

### The tests, and what makes each one able to fail

Three tests, and the third is the one that matters:

1. `method: random` under an otherwise-well-formed `allocation: between` + `sweep.groups` config →
   `E-DATA-ASSIGN-DRAWN` in `codes(...)`.
2. `method: blocked` → same.
3. **The control: `method: by_attribute`, byte-identical config apart from the method string,
   asserts `E-DATA-ASSIGN-DRAWN not in codes(...)`.** A bare `not in` assertion passes for a config
   that failed to load, for a typo'd fixture, for a harness that bailed three checks earlier — four
   probes in this project have already reported nothing for *every* input. So the control **must
   also assert something positive about the same result**: that the config is otherwise clean of
   `E-DATA-ASSIGN-*` codes AND that a code you know it does produce is present (today
   `E-DATA-ASSIGN-UNSUPPORTED` still fires on any truthy `assign` — task 17 retires it, so pick
   something that survives, or assert `findings` is non-empty for a reason you name in a comment).
   State in the test's docstring what number or string discriminates it.

**Mutation, per the global constraints — each value separately.** Narrowing the refused set to
`("random",)` must fail the `blocked` test and **only** it; narrowing to `("blocked",)` must fail
the `random` test and only it. If one mutation kills both tests, or kills neither, the tests are not
discriminating between the values and must be rewritten. Delete `__pycache__` between mutation and
revert; verify the revert by running the tests, never by `git status`.

**Do not touch task 17's work.** `E-DATA-ASSIGN-UNSUPPORTED` stays exactly as it is; a config with
`method: random` reports both codes in this build and that is correct.
