## Task 5

**Ruling AA, and the lockfile ranking.**

> **RULING AA (binding, restated here):** the two lockfile sources are **both real** and `reproduce` must
> not prefer silently. Measured: a run records an **untracked** `uv.lock` into `environment/uv.lock`
> while `git clone` of the recorded commit has **none** — the dirty gate's pathspec is the hashed trees
> only. Decide which it restores from, and **make the other one's absence or disagreement a reported fact
> rather than a silence.** **Cost if wrong:** an environment restored from the wrong lockfile reproduces
> numbers nobody can trace.

Design Decision 3's ranking, in order, each step printing what it found:

1. `uv_lock_hash` is `null` → `E-REPRODUCE-UNLOCKED`, exit `1`, **checkout kept** (task 6 owns the
   ruling; this task owns the branch).
2. The byte copy is reachable — `environment/uv.lock` **beside the operand**, i.e. the run-directory form
   → check its sha256 against `uv_lock_hash` (`E-REPRODUCE-LOCKFILE-EDITED` if it fails), copy it into
   the checkout, and report the clone's own lockfile as *absent* / *identical* / *DIFFERS*. **Never
   overwrite without the line.**
3. Unreachable — the bundle form (correction 6: the recorded path is a **dangling** reference) → the
   clone's committed `uv.lock` is used **iff** its sha256 equals `uv_lock_hash`, and the line says so.
   Otherwise `E-REPRODUCE-LOCKFILE-UNREACHABLE`, exit `1`, checkout kept, the message naming **both**
   the recorded digest and what the clone holds.
4. `environment/pyproject.toml`, where reachable, compared against the clone's byte for byte and reported
   *identical* / *DIFFERS* — **before** `uv sync`. It is **not copied in** (it is a tracked file at the
   recorded commit, and overwriting the commit's own manifest with an uncommitted edit would make the
   checkout a tree that exists nowhere) and it **does not refuse**: it is the input that explains a
   `uv sync --locked` failure a reader would otherwise guess at. Correction 5: `provenance.environment`
   names no `pyproject.toml`, so this file is found by convention, not by record.
5. `uv sync --locked` in the checkout. Failure → exit **`5`**.

**Fixtures G, H, I, J, L.** **Fixture H is not optional**: without a bundle whose lockfile *is* committed,
Fixture G proves only that something refused, and *"a bundle can never sync"* and *"a bundle syncs when
the lockfile travels with the commit"* stay indistinguishable. **Fixture I's two lockfiles differ by
construction**, which the single-lockfile fixtures cannot supply. **Fixture J asserts the `DIFFERS` line
AND its position before the `uv sync` line** — the ordering is the whole point of step 4.

**Mutations:** prefer the clone's lockfile over the byte copy (Fixture I); use the byte copy without
checking its digest (a Fixture I arm with the copy edited after the run); accept the clone's lockfile in
the bundle form without comparing digests (Fixture G, with H as the success control); skip the
`pyproject.toml` comparison (Fixture J).

**Must not touch:** `uv_support.py`'s `uv_lock_info` (it answers *what does this repo hold now*, which is
a different question), `run_record.py`, guard-pin arm F.

---

