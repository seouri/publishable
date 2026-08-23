## Task 14

Both consistency passes, and the dated entry.

1. **Mechanical, over every `*.md` this branch edited**, written as a throwaway script: every relative
   link and `#anchor` resolves, no two headings in a file produce the same anchor, every table's rows
   match its header's column count with no empty row, no trailing whitespace, no tab, no invisible
   unicode. **Skip fenced blocks** — the docs contain markdown inside markdown. **Prove the checker
   can fail** before trusting it: a records task in this family disclosed eight false positives on
   first run.
2. **Cross-document, over the four documents only.** The classes that actually drift: the shared
   worked example (`cohort-pilot`'s 20 step directories is a **new** figure in it and must appear
   nowhere else in a contradicting form), config completeness (no field added), enum comments
   (`apparatus.PHASES` versus § The apparatus files — see task 13), declared-versus-derived, versions,
   and prevented mistakes. **The development record is exempt from both passes and must not be
   retro-edited.**
3. **§ Executability on this build** — one dated entry, *"Measured on 2026-08-23 against commit
   `<sha>` — after H9a"*, the **four-row table repeated character for character** from the preceding
   entry, and **no fifth number**. Derive each row rather than repeating the derivation: `dry-run` and
   `draft` neither run at `validate` nor are called from a step, the extraction is behaviour-preserving,
   nothing here reads an upstream, nothing here chooses an interval construction, and every one of the
   nine configs validates against `generic`, whose `apparatus_probe` resolves to `None`. **H9a unblocks
   ZERO configs**, and the reason is structural: both commands are second entries into a sequence these
   configs already reach or do not. Extract the preceding table programmatically and **diff it byte for
   byte** rather than retyping it.
4. **Three live claims in that same analysis go false and are corrected by appending, never by
   retro-editing a dated entry**: *"`draft` … does not dispatch in this build"*, *"`dry-run` prints
   specified but not built"*, and *"`dry-run` prints … where every artifact will land"* — the last
   being Ruling R's third home.

**Do not assert an ordinal.** *"the seventh consecutive entry"* is the easiest kind of claim to carry
without checking; derive it from the diff or omit it.

**Must not touch:** any `src/` or `tests/` file. If a pass finds a code defect, that is a finding to
report.
