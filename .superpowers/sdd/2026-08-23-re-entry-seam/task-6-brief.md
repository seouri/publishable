## Task 6

**Design Decision 9 binds this task.** § Draft runs reads *"Draft runs are recorded with `draft: true`
and `git.code_dirty: true`"*, and the second half is false of the code: `code_dirty` is computed from
the tree, so a draft of a clean tree records `false`. **Correct the document, not the code.** Forcing
the flag would make a `provenance` figure lie about the tree and would break `diff`'s `git` comparison
between a clean draft and the `run` of the same commit.

**Fixture R** — `draft` on a **clean** tree, outside this repository. The fixture must **verify its own
premise**: run `git status --porcelain -- src templates` inside it and assert it is empty, *then*
`main(["draft", cfg])`. Assert `record["draft"] is True` and
`record["provenance"]["git"]["code_dirty"] is False`, and assert the task-3 notice was **not** printed
— on **stderr**, the stream it writes to.

**Then edit § Draft runs**, minimally: `draft: true` is unconditional and is the flag every reader keys
on; `git.code_dirty` records what the tree was. Say which is which. **Prefer deleting the false half
of the conjunction to rewriting the sentence around it** — a rewrite invents, a deletion cannot.

**Sweep before you edit.** Grep `code_dirty` over `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md` and
`docs/feasibility-llm-growth-studies.md`, **named individually, never `*.md`**, and attribute every
hit. Two known homes: § Draft runs and § The two files' `run.yaml` example comment. **Sweep for the
claim, not for the file the claim was first noticed in** — three sweeps in one slice stopped one file
short.

**Mutation:** force `code_dirty=True` under `draft` → Fixture R must fail. Its premise is verified
clean, so the two branches differ.

**Must not touch:** `provenance.py`, `cli.py`, § Operation commands' rows.

---

