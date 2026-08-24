## Task 18

**Pointer: both consistency passes, and the design's § Is this additive? is what you check the records
against.**

- **Mechanical**, over every `*.md` this slice edited: every relative link and `#anchor` resolves; no
  two headings in a file share an anchor; every table's rows match its header's column count and no row
  is empty; no trailing whitespace, tab, or invisible unicode; `×` not `x`; hyphens, never en dashes,
  in anything that becomes an anchor. **Skip fenced code blocks in all of these.** Write the checks as
  throwaway greps or a short script; the repo ships no tooling. **Prove each sweep can fail** by running
  it against a string known to be present.
- **Cross-document**, over the four documents only — the feasibility analysis is exempt from this pass
  and subject to the mechanical one in full. Config completeness (`identity.json` is not a config
  field, so § The one config file does not move — check and say so), enum comments, schema fields in
  prose, declared-versus-derived (`attempts` is now **derived**: no passage may show it as an input),
  versions, and the shared worked example.
- **After removing any string, grep the four documents, `CLAUDE.md`, and the feasibility analysis for
  what should no longer exist** — `attempt` and `n` in the ledger example are the two this slice
  removes.
- **Check the disclosure against the code**, item by item, and correct it by appending if any item is
  wrong. **H9a's gate found a disclosure that was WRONG, which is worse than none.**

**Must not touch:** `src/`; any arm; the development record's dated entries — **append a correction,
never retro-edit one.** `spec-defects.md` is the single exception, being a live list where a closed gap
is struck.

**Report:** what each pass checked, what it found, and — for every sweep — the string, the file list,
and every hit attributed.
