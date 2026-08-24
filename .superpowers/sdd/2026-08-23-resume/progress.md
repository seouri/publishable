# H9b — `resume` — the ledger

Branch `h9b-resume`, off `main` at the H9a merge. **18 tasks in eight batches, every batch reviewed.**
H9 was scoped at 49 tasks in four parts; H9b is the hardest, because `resume` is the command that
**compares recorded against recomputed** — and the scoping measured that § Resuming's documented
comparison **had no operand**: a real crashed run directory holds no `run.yaml`, so only the run ID's
7-hex prefix survived.

Three controller rulings: **V** (`resume` compares against something `run` made durable **before**
executing, and refuses by name when it is absent), **W** (`resume` takes over a lock whose holder is not
alive, and refuses `E-RUN-LOCKED` when it is — **no flags, ever**), **X** (`E-RUN-LOCKED` appears in none
of the four documents and H9b documents it).

**The liveness protocol was designed by falsification, which is the entry to carry.** Two candidate
protocols were **falsified on trial 0** by five-process probes — rename-as-mutex produced **four
winners**, scan-then-claim **two**. The shipped one — an exclusive `O_CREAT|O_EXCL` token as the mutex,
released in a `finally`, with the holder judged dead **only** on `ProcessLookupError` from
`os.kill(pid, 0)` for a pid recorded against this `gethostname()` — held **60 trials × 5 processes with
zero violations**, and deleting the token produced two winners by trial 22. **A lock is the one thing in
this project that cannot be pinned by a mutation alone**, and running the race is what separates a design
from a hope. `lock` gains `started_at` for the diagnostic and **the liveness test deliberately does not
read it**, so PID reuse refuses rather than guesses.

## Batches 1 and 2 — tasks 1–4 — the pin and `identity.json`

Commits `811feee` (the pin), `ff942ef`, `c7bbd64` (**the write site**), `f70f63f` (**the normalization
list, committed before the comparison ran**), `61532a1`, `b9e1560`, review `4ed2fa5`/`9fdda34` (**all four
PASS**, two Majors, eight Minors), controller routing commit. Suite 3019 → **3053**, plus **two strict
xfails**.

**Ruling V's answer: `<run_dir>/identity.json`**, five keys, written inside the lock after
`environment/repo_root.txt` and before `sweep.yaml` — `code_hash`, `parameters_hash`, `uv_lock_hash`,
`config_path` (repo-relative, **containment-checked on read**) and `draft`. `input_manifest_hash` is
**deliberately absent**, because `manifest/input.json` is the operand rather than a hash of one. Absent
file → `E-RESUME-NO-IDENTITY`, **no fallback to the run ID's hash prefix** — *a run directory that cannot
be resumed and cannot say why is worse than one that refuses loudly.*

**The artifact change is fully attributed, and the method is the point.** The normalization list was
committed **before** the comparison ran — verified by commit order **and** by byte-comparing it against
HEAD — and the reviewer's own two-sided run gives `run.yaml` **94 leaves, zero differing**, the tree
differing by **`identity.json` alone**, `sweep.yaml` byte-identical, the ledger key-for-key identical,
stdout/stderr/exit identical. An `input_manifest_hash` difference **was attributed by measurement rather
than waved through**: the manifest holds relative paths and `st_mtime_ns`, so `cp -p` before both runs
makes the hashes byte-equal. **An unattributed hash difference in a slice about identity would have been a
Critical.**

**Correction 22 killed a ground before it could ship**: `json.dumps` emits bare `NaN`/`Infinity` and
`coerce_scalars` passes them through, so *"serializable by invariant"* was **false** — and what is written
now survives a round-trip actually performed rather than argued.

**Major 1 is a failability claim citing the wrong mutation.** The report offered task 3's M6 as proof arm B
can fail; M6 fails four other tests and **arm B stays green** — which the report's own task-3 section says
three sections earlier. The reviewer ran the honest mutation (delete the write) and arm B fails first.
**An arm whose assertion moved needs the mutation that fails IT**, not the nearest one to hand.

**Major 2 is the recurring shape and it now has a third form: three escalations lived only in a report.**
The five `reference.md` edits the count change actually needs, fixture B's **confirmed-unreachable**
collision, and the third `repo_root.txt` reader — none reached a brief, a live task section, or
`spec-defects.md`. *A ledger line saying "filed" is not a filing; neither is a dispatch line; and neither
is a report's own escalation.* All three are now routed: two as **appended amendments inside the task
sections that own them**, one as a filing whose reason is that **three copies of one refusal have already
drifted in one keyword.**

**One good judgement worth naming.** Arm C's editor clause read `NONE`, and the batch re-aimed **only the
clause**, changed no assertion, and **stated the discrepancy** rather than stopping on a false blocker or
self-authorizing on the grounds that the name must be a slip. **That third option is the right one**, and
the design's parenthetical — which named a task that legally cannot edit those arms — is corrected by
appending.

## Batches 5–8 and the whole-branch gate

Commits `1253a3b`–`afc6a05` (tasks 10–13), `04cad73` (**the lock**), `8963071` (**`resume` flips to
built**), `d9b82c6`, `160887d`, `10ba559`, `6ddd882`; reviews `bd2b4de` (**tasks 10–18 PASS**, gate
**HOLD** on four Majors), fix round `b19f1e1` / `4efa280` / `a8bf7a6`. Suite **3132 passed, 1 skipped, 2
xfailed** against `main`'s 3019 — **+113 collected, attributed file by file, zero tests removed.**

**A crash-and-resume produces the record an uninterrupted run would**, verified through the installed
console script against a straight-through control: `run.yaml` **98 leaves, key order identical, ZERO value
differences**, hashes equal **unnormalized**, four ledger lines each. The one clause: the crash left the
interrupted triple no ledger line, so `attempts` is 1 on both sides — **`attempts` reaches 2 only for a
re-executed triple**, which is a disclosed item with its own pin.

**The lock's race was re-run against the SHIPPED code and the criterion itself was the finding.** The
design's own probe criterion — *"two winners per trial"* — **flags the correct protocol**, because a winner
releases the lock when its run ends; the violation is **two holders at one time**. And **without a stagger
the token-less control violates nothing**, so an unstaggered control cannot fail at all. With those two
corrections: detector self-test **60/60**, token-less control **0/60 unstaggered and 60/60 staggered**,
shipped protocol **0/60 and 0/120** with the stagger inside the real window. **A control that cannot fail
is not a control** — and here the criterion, not the harness, was the thing that could not fail.

**The record loss is closed at exit 4, and the exit code was derived rather than chosen.** § Exit codes
gives `1` to a changed fact *"caught before the first execution ran, which leaves nothing to mark `failed`
at all"* — **false once there are prior results** — and `5` is the retry class; `4` follows from
`run_status`'s shipped fold and is the same answer H7d Part B gives a mid-plan move with at least one
result. **No code minted.** A resume whose apparatus moved now writes `run.yaml` carrying the status and
the moving observation, which is H7d Part B's own rule — *a stop must be legible from the artifacts* —
applied to the one surface that had been discarding them.

**Major 3 is the gate's best find in four slices, because closing it uncovered a coverage loss nobody
suspected.** `tests/test_freeze.py`'s `_assert_refused` **never read its `code` argument**: renaming a code
to a bogus string left that file at 42 passed. Twenty arms asserted *that* a refusal happened, never
*which*. Fixing the helper turned **5 failed** into **25 failed** — and **four of the twenty had been
stopping at `E-FREEZE-CONFIG-EDITED`, a gate this very branch minted**, which precedes the others, so
`E-TEMPLATE-UNKNOWN`, `E-TEMPLATE-INSTALLED-UNSUPPORTED` and `E-FREEZE-PLAN-MISMATCH` had **no coverage at
all.** **A helper that ignores an argument does not merely weaken its callers — it hides what they stopped
testing**, and the fix was zero tests added or removed. An `ast` sweep for the shape (a parameter whose
name contains *code*, never loaded) found one more hit in `tests/` and none in `src/`.

**Two Majors were sentences denying what their own file had just built.** `E-RESUME-LEDGER-UNREADABLE`'s
row said *"Three faults, one code"* and **denied the fourth site by name** — re-derived by grep as four —
and `command_resume`'s docstring said *"Decision 13 is NOT implemented here"*, *"`resume` is not
dispatched"*, *"the containment does not exist yet"* and *"Task 16 owns building it"*, **all four false at
HEAD and contradicted by the same docstring's closing sentence, eighteen lines above the containment
itself.** Deleted, not rewritten. **That is the fourth consecutive slice in which a sentence went false
under its own slice's later change.**

**And two brief-supplied figures did not survive grepping** — *"21 call sites"* is **20** (the review's
grep counted the `def` line) and *"thirteen codes … every one of the fourteen"* is **fourteen codes,
fifteen minted, fifteen rows**, which only became legible once **each figure carried its noun.** A count
without a noun is not a claim anyone can check, which is why two of them disagreed for a whole slice.
