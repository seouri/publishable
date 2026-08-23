# H6b — the environment record and the diagnostic debt — the ledger

Branch `h6b-environment-record`, off `main` at the H6a merge. **11 tasks in six batches, every batch
reviewed.** Additive throughout: no shipped key's contents move, and the design derived that rather than
assuming it — **no hash reads the record**, measured, which is what makes the additive framing true.

Four controller rulings arrived with the design: **N** (the charter widens to two undocumented codes, not
three and not nine), **O** (`hardware` carries `cpu_count` and not `gpu`), **P** (no new `W-` for § Templates'
*"goes dirty at `validate`"*, and the sentence stays), **Q** (`os` and `hardware` are not redacted; `hostname`
is). H6a's rulings A–M still bind where cited.

**The plan corrected the controller's own arithmetic before a single task ran.** Ruling N said *"take these
three, leave six"*; correction 18 measured **five**, not six — nine minus `E-CODE-DIRTY` (already given its
row by H6a's batch 4), minus `E-EXPERIMENT-UNKNOWN`, minus H6b's own two, with `E-STEP-EXISTS` never having
been one of the nine and counted in by both first drafts.

## Batch 1 — tasks 1, 2 — the pin, and the shared worked example

Commits `8019578` (six arms named, arm T built), `2ed64da` (Ruling O in § The two files), `110350c`,
review `b65f67e`. Suite 2963 → **2964**. **Both PASS, two Minors, both miscounts.**

**The pin was captured against the shape task 3 will produce, not the shape that exists** — which is the
direct answer to H6a's batch 2 Major, where arms captured against a **superseded signature** forced a later
task to choose between a broken import and an unauthorized edit. **Five of the six arms have no authorized
editor**; only arm P has one, and it is task 3's.

**The reviewer checked the distinction that matters for a pin: built versus merely named.** Arm T is new
and was independently proven able to fail — mutating `git_provenance` to raise before the commit check
fails it. Arms P, Q, S and U are **pre-existing pins with docstring-only edits**, all re-run; arm R was
confirmed **unaffected by Ruling O's edit** by counting literal matches against both the old and the new
`hardware` line, which is correction 16 verified rather than trusted. **A named arm with no test is not an
arm**, and that question was asked of each of the six.

**Ruling O's edit is the first change to the shared worked example in this slice family, and it was swept
as one.** `gpu`/`A100` across all four documents plus `CLAUDE.md` plus the feasibility analysis: the only
hit is an unrelated hostname and the task's own new prose. The rejected alternative is worth keeping —
sourcing `gpu` from the apparatus **inside** that example would have given `cohort-pilot` a probe, and
§ The apparatus core can only observe says the worked example declares none and records `apparatus: null`.
**A ruling that fixes one document's example can contradict another document's claim about the same
example**, and only sweeping for the *claim* rather than the *key* finds it.

**Both Minors are miscounts** — a 26 that is 25, and a per-file diff stat off by two in a correct total —
bringing this family to **eight**, none of which has ever changed a conclusion.
