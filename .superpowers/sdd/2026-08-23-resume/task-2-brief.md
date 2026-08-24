## Task 2

**Pointer: Ruling V binds this task (design Decision 1). Read it before writing a line.**

**Ruling V: `resume` compares against something `run` made DURABLE BEFORE executing; if that thing is
absent, `resume` refuses with a named code rather than guessing.** This task defines the artifact and
nothing else — the write site is task 3 and the reader is task 8.

Add to `run_identity.py` (beside the lock, which is where run-identity facts live — not `cli.py`,
which is a dispatcher):

- `IDENTITY_FILE = "identity.json"`.
- `identity_document(*, code_hash, parameters_hash, uv_lock_hash, config_path_rel, draft) -> dict` —
  the five keys in that order, `uv_lock_hash` `None`-able, `config_path_rel` a POSIX-separated
  relative string.
- `read_identity(run_dir) -> dict` — raises `ContractError(code="E-RESUME-NO-IDENTITY")` when the file
  is absent, will not parse, is not an object, or lacks any of the five keys.
- `config_path_for(run_dir, repo_root, document) -> Path` — resolves `document["config_path"]` under
  `repo_root` and **refuses a resolved path that is not contained by it**, and refuses a missing
  `repo_root.txt`, an empty one, or one naming a non-directory, with
  `ContractError(code="E-RESUME-NO-CONFIG")`.

**The containment rule is containment ONLY.** Forward separators stay legal; an absolute recorded path
is refused; `..` segments are refused by the containment check rather than by inspecting the string.
This is H8a's rule and the reason is its own: *a guard's rule may be narrower than the gap it closes*,
and **a mutation widening it must fail a positive control** — write that control, a document whose
`config_path` is `../../secret/config.yaml`.

**Write no comment claiming a guarantee this code does not provide.** In particular do not write that
the containment check makes the config safe to read: a step can `open()` anything regardless, and the
rule is containment of the *recorded name*, nothing more.

**Must not touch:** `cli.py`, `provenance.py`, `freeze.py`, any `*.md`, any existing test's
assertions.

**Mutations:** drop the containment check (caught by the positive control); accept a document missing
`draft` (caught by a `read_identity` fixture whose document has four keys).

---

