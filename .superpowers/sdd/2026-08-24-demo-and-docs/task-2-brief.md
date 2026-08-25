## Task 2

**Binding corrections: 17, 18, 30.**

**The managed-region machinery.** Create `src/publishable/docs.py` with the parser and the rewriter,
and nothing that dispatches. No command wiring in this task.

> **RULING EE (binding, restated here):** `docs` rewrites **only what a region encloses**, and a region
> it cannot find is a **named refusal, never a silence** — *a command that silently rewrites nothing
> looks identical to one that worked.* **Cost if wrong: a user's hand-written prose outside a region is
> destroyed, which is unrecoverable and is why the markers exist at all.**

Build:
- `regions(text) -> dict[str, tuple[int, int]]` — region name to the half-open **line** span strictly
  between its `begin` and `end` markers. **Lines inside a fenced code block are not scanned**: the
  documents contain markdown inside markdown, and a marker there is content.
- `rewrite(text, name, body) -> str` — replaces exactly that span, leaving every other byte, including
  both marker lines and the trailing newline convention, untouched.
- The five refusals of design § 3's table, each raised as a `ContractError` with its code.

**The four managed region names are `overview`, `credentials`, `experiments`, `templates`** — the first
three from § The generated README, the fourth from § Templates.

**Fixtures:** design § 9's fixture B (five malformed READMEs, one condition each, **each carrying one
well-formed region beside the broken one** so a refusal cannot pass by the file being empty) and
fixture C (all four regions, prose above/between/below, **and a line containing a marker spelling
inside a fenced block**).

**Mutations:** design § 10 rows 1, 2, 3, 4. Row 3's assertion must check **the code and the stderr
line**, never only the exit code.

**Must not touch:** `cli.py`, `scaffold.py`, any generator, any document.

---

