## Task 9

**Ruling BB's second half: `run`'s first probe compares against `apparatus.expected.json`.** **This is
the behaviour change to a shipped command.** Guard-pin arm C's sole authorized editor is **this task**.

> **RULING BB (binding, restated here):** `apparatus.expected.json` is a **comparison, not a gate** — for
> `reproduce`. On another device the apparatus will differ, and that is expected rather than exceptional:
> a GPU model, a hostname, an OS. So **`reproduce` reports apparatus differences and does not refuse on
> them**, while **the run it then performs is an ordinary `run` under the ordinary gate**. **Cost if
> wrong:** either a reproduce that cannot run anywhere, or one whose numbers came through an apparatus
> nobody recorded. Task 10 owns `reproduce`'s half; **this task owns the ordinary gate's half**, which is
> where the comparison actually happens, and § Reproducing on another device is explicit that the first
> probe *"fails on any difference, at the same volume as a lockfile mismatch"*.

**Do not write a comparison** (correction 10). `Observations.record` followed by `.changed` **already is**
the gate — per condition, first-*answered*, `null → value` and `value → null` both passing,
reflexivity-safe for `nan` — and `apparatus.replay_ledger` is the shipped precedent for reconstituting one
from a file:

```python
def expectation_from(path: Path) -> apparatus.Observations:
    """The recorded facts as an `Observations`, so the SHIPPED gate is the
    comparison (§ Corrections 10). Never a `!=`: `null -> value` passing is
    what § Reproducing on another device calls "more evidence rather than
    less", and `_unchanged` is what keeps a constant `nan` from
    contradicting itself.

    A SECOND object, asked only for `changed`. Seeding the run's own
    `Observations` -- the shape `Resumed.baseline` uses, where the counts
    were real probes -- would bump `_total_counts`/`_null_counts` and make
    `provenance.apparatus.unobserved` and `W-APPARATUS-UNANSWERED` claim
    probe calls this run never made (§ Corrections 11). That is the mutation
    Fixture Q exists to catch, and it is what a naive implementation IS.
    """
```

**A distinct code, `E-APPARATUS-UNEXPECTED`, because the remedy is distinct.** `E-APPARATUS-CHANGED`
means *the apparatus moved during this run — stop*; this one means *this apparatus is not the recorded one
— accept that this is not a reproduction, or edit `apparatus.expected.json`, which § Reproducing says you
may*. One code covering both would be H4d's *one code, five faults* again.

**Memberships, and they are opposite** (correction 12):

- `STOP_CODES` **gains** it → post-edit set `{"E-APPARATUS-RAISED", "E-APPARATUS-CHANGED",
  "E-APPARATUS-UNEXPECTED"}`. **This is guard-pin arm C and you are its sole authorized editor: one
  member added, none removed, nothing reordered, matching the design's advance spec byte for byte.**
- `APPARATUS_CODES` does **not** — the loop breaks on a `STOP_CODES` member before `command_run`'s
  containment filter is reached, which is `E-APPARATUS-CHANGED`'s own documented reason. **Arm D's two
  shipped assertions have editor NONE**; you may **add** a sibling
  `assert "E-APPARATUS-UNEXPECTED" not in APPARATUS_CODES`, and adding an assertion is not editing one.

**No exit code is minted:** `1` before the first execution, `4` once there are results, from
`run_status`'s shipped fold — the same derivation H9b recorded, not a choice.

**The file's location is `<config_dir>/apparatus.expected.json`**, which § Reproducing specifies. It sits
outside `src/**` and `templates/**`, so neither `code_hash` nor the dirty gate sees it — and the ground
is a **measurement**, not the pathspec: an untracked `uv.lock` at a repo root left
`git status --porcelain` reading `?? uv.lock` and the run exiting `0` (design § 0.1). Reasoning from the
pathspec alone would be answering with a proxy.

**Fixtures P and Q. Fixture P's four arms cannot be collapsed**: a moved value fails, `null → value`
passes, `value → null` passes, and a fact present for one condition and absent for the other is compared
per condition. **Three of the four are the tolerance § Reproducing calls *"more evidence rather than
less"***, and a fixture with only the failing arm leaves every tolerance untested. **Fixture Q is the arm
that catches this task's rejected alternative**: seeding the run's own `Observations` inflates
`unobserved.total_probes` while every arm of P stays green.

**Mutations:** compare with `!=` (P arms 2 and 3); compare against the whole `facts` rather than per
condition (P arm 4 — P has two conditions with **different** facts); reuse `E-APPARATUS-CHANGED` (P arm 1,
which asserts the identifier); add the code to `APPARATUS_CODES` (arm D's addition plus P arm 1); remove it
from `STOP_CODES` (P arm 1 — the run would finish `completed`); seed the run's own `Observations`
(Fixture Q).

**Must not touch:** `Observations.record`, `.changed`, `.facts_document`, `.unobserved`,
`.warn_unanswered`, `replay_ledger`, or `Observer`'s existing signature beyond one optional parameter.
Arm A's cited arms must stay green: **no run without the file may change in any way.**

---

