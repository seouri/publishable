## Task 9

**Binding corrections: 24.**

**The bytecode-cache fix, at all three call sites, closing two filings.**

Replace the implicit loader with an explicit `importlib.machinery.SourceFileLoader` at
`templates/discovery.py::_import_file`, `report.py::render_with_override` and
`base_experiment.py::load_experiment`. **One root cause, three call sites** — the filing's own *check
its owner must make* requires the same option at all three in one pass.

**Option (b), documenting the weaker per-process property, is rejected by design Decision 10, and this
is the last chance to reject it:** H8b declined it, the filing was re-owned to H9 for that reason, and
there is no owner after this slice. **`sys.dont_write_bytecode = True` is also rejected**: it is
module-global and changes compilation for every concurrent import in the process, which is a proxy for
the question.

**Fixture E (design § 9):** the filing's own recipe, **at the same byte length** — a differently-sized
second file is picked up even unfixed, so it tests nothing.

**Mutations:** design § 10 rows 5 and 6. **Row 6 is the one that matters**: revert the fix at exactly
one of the three sites and confirm a distinct test fails for that site. *A sweep that stops one file
short* has happened three times in one slice here.

**Do not** rewrite the two `spec-defects.md` entries — task 14 strikes them, with the entries' own
claims re-read against the code you changed.

---

