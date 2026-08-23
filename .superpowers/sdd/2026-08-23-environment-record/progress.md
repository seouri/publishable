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

## Batch 2 — task 3 alone — the write

Commits `3b583f2` (the three keys), `354bb46` (**a controller ruling on guard-pin arm S**), review
`fb41816` (**PASS**, no findings, one process note). Suite 2964 → **2969**.

**Capturing the pin forward worked, and this batch is the direct counter-example to H6a's batch 2 Major.**
Arm P was captured in batch 1 against the shape task 3 would produce, with its post-edit state written
down before the task existed; the diff matches that spec **byte for byte** — three pops, three assertions,
the `==` literal identical. H6a's arms were captured against a **superseded signature** and forced a later
task to choose between a broken import and an unauthorized edit. **The difference is one batch of
foresight, and it is cheap.**

**The other half of that discipline also worked, and it is the more valuable half: the task left a test
FAILING rather than self-authorizing an edit.** Its write made real records carry `hostname`, which
falsified the premise **guard-pin arm S** rested on — *today's real records never carry `hostname` at
all* — and arm S has **no authorized editor**. The task stopped, named three options, and reported. That
is exactly the route H6a's batch 2 Major said to use and H6a's batch 3 first used; **it now has an
instance where the alternative was to leave the branch red, and it still held.**

**The ruling kept the property and changed only its source.** Arm S was always testing that redaction does
not **invent** `hostname`; the record now has the key **deleted explicitly** rather than absent by
accident, with the assertion byte-identical. The reviewer re-derived the equivalence — `dict.get` on a
missing key and on an explicitly deleted one both return `None` — and **re-ran the mutation the arm exists
to catch**: making the redaction unconditional fails that one test and nothing else, before and after the
edit. *An arm whose premise its own slice falsified is not a weakened pin if the property survives and the
mutation still bites.*

**Two facts worth carrying about the write itself.** `socket.gethostname()` is called from two **sites**
but they are one function, so it is **not** the two-sources fault H6a spent a Major establishing —
checked rather than assumed. And **`cpu_count: null` is inert downstream**, because **no reader of
`hardware` exists anywhere**: `diff.py` reads only `uv_lock_hash`, `study.py` only `hostname`. That is
worth knowing before someone writes the first reader.

**And a stale comment is already waiting.** `study.py` says `provenance.environment.hostname` *"is never
written today (measured at …)"* — **task 3 falsified it**, it is task 7's by plan, and it is the fourth
sentence in two slices to go false under its own slice's later change.

## Batch 3 — tasks 4, 5 — the redaction reason and the two error rows

Commits `b5a3da0` (Ruling Q's reason plus the end-to-end bundle pin), `9e292ea` (Ruling N's two § Errors
rows), `991c849`, review `1927b21` (**both PASS, no findings**). Suite 2969 → **2971**.

**The convenient answer was checked and turned out true, which is worth recording precisely because it was
convenient.** The report claimed correction 15's gap — *no test asserts either git code through
`main([...])`* — was **already closed by arm T**, built in batch 1 before task 5's brief existed. That is
the most self-serving possible finding, so the reviewer ran arm T standalone, confirmed by `git log -S`
that it predates the brief, and then **mutated the `E-GIT-NO-COMMIT` raise site to a silent fallback**:
arm T fails on `assert 'E-GIT-NO-COMMIT' in ''`. **It exercises the code through the console entry rather
than passing vacuously** — which is the difference between a closed gap and a gap closed by assertion.

**Ruling N's rows account for a swallow, not just a raise.** `E-GIT-NO-REPO` has **one raise and six reach
paths, three of them deliberate swallows** — and *a swallow is part of a code's behaviour*, so a row that
describes only the raise would be narrower than its code, which is the exact shape that produced a
whole-branch Major on two sub-slices and shipped twice in a third. Both codes' reach paths were
re-derived by independent grep, and **the placement question was answered from the table's own scope
sentence rather than from the design's instruction** — the correction of H6a's batch 4, where a review
settled the same question by citing the design.

**Ruling Q's pin is the point and it was proven able to fail.** A real bundle built outside the test suite
carries `hostname` redacted and `os`/`hardware` verbatim; **extending the redaction to cover `os` fails
the new fixture.** The `hostname` wiring had been written against a key nobody wrote until task 3, so
until this batch there was nothing to pin. And § What `study add` redacts now says **why** — redaction is
for identity and credentials, and a bundle reader needs the platform that produced a number — so the next
reader does not re-litigate it.

**One process note worth keeping: a reviewer's own CLI probe wrote stray `configs/` and `src/cohort_pilot/`
into the repo's working tree**, caught before the gates were taken as final. A probe that runs a creation
command inside the repo dirties the tree the dirty gate reads — **which this slice's sibling made
load-bearing** — so a probe belongs outside the repo, the same rule the bundle fixtures already follow.

## Batch 4 — tasks 6, 7 — Ruling P confirmed, three stale claims, and NO implementer report

Commits `596985a` (Ruling P confirmed, Decision 12 declined and re-owned), `1bd9483` (three stale
claims), `2a9c05b` (a follow-up deletion), review `4f891c0` (**both PASS**, one Major on process, one
Minor). Suite unmoved at **2971**.

**The implementing agent stalled — it built a monitor and waited on it, which this repo forbids in every
dispatch — and it wrote NO report at all.** Task 7's work was sitting uncommitted in the worktree; the
controller ran the gates, read the diff, and committed it. So **this batch has a review and no report**,
and the reviewer re-derived every claim in both commit messages from scratch. **That is the cost of the
stall and it is worth stating: a commit message is not a report.** What an implementer intended and did
not write is invisible, and the only way to find an unfinished clause is to diff the brief against the
diff — which is what was done here.

**§ Templates' sentence is TRUE when measured, so Ruling P stands and task 6 correctly changed nothing.**
Reproduced live outside the repo: a clean tree, `validate` exits 0, `templates/__pycache__/` and
`src/**/__pycache__/` appear untracked, and `run` then refuses with `E-CODE-DIRTY`. **A confirmation that
cannot fail is not a confirmation**, so the arm of this that mattered was building the repo whose
`.gitignore` omits that line rather than reading the sentence again. One clause **expected** to be false
— Ruling F's target — turned out **already fixed by H6a's own task 1**, so the no-op is correct rather
than a missed step.

**Two of the three stale claims were deleted and one was superseded with its date, and the distinction is
the rule.** `secrets.py` enumerated `provenance.environment`'s keys *inside* a structural claim — the
enumeration was incidental, went stale the moment task 3 wrote three more keys, and was **deleted**, since
the structural claim (*nothing here imports `provenance`*) stands alone and is what the paragraph is for.
`study.py`'s *"never written today (measured at `ebf642a`)"* was **corrected rather than deleted**: the
measurement was **true on its date**, and *deleting a true claim is not licensed by prefer-deletion* —
H6a's design ruled exactly that about `W-TEMPLATE-VERSION`. **The fourth home the reviewer swept for did
not exist**, checked newline-insensitively across `src/`, `tests/`, the four documents and `CLAUDE.md`
with a can-fail control.

**And the Minor is the rule failing in the small.** Fixture Y's docstring was told to **delete** its stale
parenthetical and instead **substituted new prose** — true, but redundant with the next sentence. Closed
by making the deletion. *A rewrite invents; a deletion cannot* is not a preference to be traded against
a marginally nicer sentence.

## Batches 5 and 6 — tasks 8, 9, 10, 11 — the records, the passes, and § Executability

Commits `2a62bbe` (`spec-defects.md`), `49c8a33` (`CLAUDE.md`), `9b7cc54` (both consistency passes),
`4a3b9fc` (§ Executability), `b1b58db`, `df1796c`, review `841eeef` (**all four PASS**, one Minor),
follow-up `1b5f0cd`. Suite unmoved at **2971**.

**§ Executability does not move, re-derived rather than repeated**, and the four-row table was **diffed
byte-for-byte** against H6a's entry by the reviewer independently of the report's own script. **Whether
`W-PARAM-UNSET` fires on those nine stays unknowable with a reason** — neither plugin is installable.

**A records task found two of its own brief's claims false, which is the third slice running where the
authorities were wrong rather than the work.** `environment` is **not** the only sub-block whose key order
matches the example — `git`'s six keys match too, and did **before** H6b — and the
`allocation`/`allocation_hash` row was **amended, never struck**, which is precisely why that entry still
read as three open rows two slices later. **An amendment left where a strike belonged is how a closed gap
keeps recruiting readers.**

**And the design's own arm count was wrong.** Decision 16 says four arms have no authorized editor; the
ledger, the dispatch and batch 1's review all say **five** — six arms, one editor, so five. The design is
a dated record and was **not** retro-edited; the count is corrected here and in the review.

**Two ordinals were asserted and then derived, which is the shape this project keeps paying for.** The
*"sixth consecutive entry"* phrase in § Executability was **asserted in the first draft** and rewritten to
be **derived** from the diff — the exact carried-summary-phrase failure that section's two dated
corrections exist about. **A number in a document is a claim, and an ordinal is the easiest kind to carry
without checking.**

**One real pre-existing mechanical defect was fixed rather than stepped around**: the feasibility
analysis' *Class-ratio* row **wrapped across two source lines**, rendering a bogus one-cell row with the
same § Executability link duplicated at the wrap — on `main` since `bc20b13`. **The wrap is the same
mechanism that hid two of a false sentence's five homes last slice**: prose that wraps defeats both a
`grep -F` and a table parser.

**The Minor is a heading disagreeing with its own body.** The root-`.gitignore` entry's heading still read
`Owner: H6b` after its own 2026-08-23 amendment re-owned it **unassigned** — *a heading naming a closed
slice reads as live work somebody holds*, which is the failure the re-owning rule exists to prevent, in
its smallest possible form. Task 8 was forbidden to touch that entry and **reported it instead of
reaching for it**, which is right; the controller closed it.

**Left for a successor with its reason: `## Cost and execution summary` sits between § Executability's
entries**, so every entry from 2026-08-20 on is structurally nested under it. Pre-existing, and repairing
it moves a heading **six links** point at — so it is disclosed rather than fixed in a slice chartered
additive.
