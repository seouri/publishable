## Task 14

**Pointer: Ruling W binds this task (design Decision 2). Read it in full — its mechanism was arrived at
by falsifying two others.**

**Ruling W: `resume` takes over a lock whose holder is NOT ALIVE, and refuses `E-RUN-LOCKED` when it
is. No flags, ever.** `--force` is forbidden by *"operation commands take paths and nothing else"*,
which also rules out a `--force`-shaped environment variable and a second positional. **The lock's job
is to stop a second CONCURRENT run; `resume` is by definition a re-entry after the first stopped.**

Build, in `run_identity.py`, in this order — **and the order is the whole of its correctness**:

1. `os.open(run_dir / "lock.takeover", O_CREAT | O_EXCL | O_WRONLY)`. `FileExistsError` →
   `E-RUN-LOCKED`. Released in a `finally` that runs on every path, `BaseException` included.
2. Inside the token: read `lock`. Absent → step 4.
3. Liveness-test. **Dead only on `ProcessLookupError` from `os.kill(pid, 0)` for a `pid` recorded
   against this machine's `socket.gethostname()`.** Held on: unparseable JSON, a non-object, a
   missing or mistyped `host` or `pid`, a foreign `host`, `kill` succeeding, `PermissionError`, and any
   other `OSError`. Held → `E-RUN-LOCKED`. Dead → `unlink(lock)`.
4. `RunLock(run_dir)`, whose `O_CREAT|O_EXCL` is still the only claim in the system.
   `FileExistsError` → `E-RUN-LOCKED`.

**Two other protocols were probed and both were falsified on trial 0** — liveness-then-`os.rename`
(four winners of four) and scan-then-claim (two winners). Both fail because a decision taken from the
directory's state is stale by the time the claim is made. **Contend first, decide second.** The token
protocol held 60 trials × 5 processes with zero violations, and deleting the token produced two winners
by trial 22. Re-run both probes yourself and report the numbers; if either disagrees with these, that is
a finding.

**`RunLock.__enter__` gains `started_at` in its JSON payload** — § One execution at a time documents it
and the code writes two keys (correction 9). It exists for the **diagnostic**, and **the liveness test
deliberately does not consult it**: say so in the code and in the document, because PID reuse therefore
reads as *alive* and refuses, which is the conservative direction. A recorded field nothing reads would
otherwise be this repo's own named defect class.

**Write the residual down rather than around it.** A takeover killed between the token's creation and
the lock's leaves `lock.takeover` behind and every later `resume` refuses until it is removed. That
window holds two syscalls and no user code — which is why nothing else goes inside it — and the
`E-RUN-LOCKED` row names the file and the remedy. **A safety argument in a comment is a claim**: if you
write that the window is small, make it fail.

**You unblock guard-pin arm G**, which task 1 left `xfail(strict=True)`. Remove the marker and nothing
else about it.

**Must not touch:** `RunLock.__exit__`; `allocate_run_dir`; `cli.py`; any `*.md`; any other arm.

**Mutations:** delete the token's exclusive create (arm G — deterministic via its barrier, and the
five-process probe as corroboration); treat unparseable JSON as dead (a fixture arm); consult
`started_at` (**named blind in advance** — no fixture can force a recycled pid; the owed replacement is
a structural assertion that a lock with **no** `started_at` and a dead pid is taken over, which a
`started_at`-consulting test would have to refuse).

---

