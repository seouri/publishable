## Task 11

**Design Decision 12 binds this task, and it corrects a premise you would otherwise write.** *Creates
nothing* is scoped to **`output_dir`**, not to the repository. `dry-run` imports the entrypoint and
runs `discover_local`, which writes `src/**/__pycache__/` and `templates/__pycache__/` — measured live
by H6b batch 4 for `validate`, and § Templates' *"goes dirty at `validate`"* is the shipped sentence
about it. **A repo-wide byte-identity assertion fails, and the fix would be to weaken the assertion**,
which is the worst of the three outcomes. Scope the arm, name `__pycache__` as the excluded residue
with that citation, and say in the code why that scoping **is** what the promise means: it is about the
artifacts of a run, and a bytecode cache is not one.

**Fixture Y.** A recursive `(relative_path, size, sha256)` snapshot of `output_dir` before and after
`main(["dry-run", cfg])`, asserted equal, plus the absence of any `run_*` directory. Then the second
arm: a run directory holding a **live `lock`** (write the lock file by hand, as `freeze`'s own tests
do — do not kill a real run), and `dry-run` against the same config completes at its normal exit code
and takes no lock. § One execution at a time says pointing a read command at a live run is *"as
ordinary as reading the ledger"*, and `dry-run` is the stronger case because it takes no lock at all.

**Mutation:** have `command_dry_run` create `output_dir / "scratch"` → Y must fail. And confirm the
snapshot helper can fail at all by running it against a directory you *do* write to — *prove every
sweep can fail* applies to a checker as much as to a claim.

**Must not touch:** anything under `src/` except the notice-free path you are asserting about; no
`*.md`.

---

