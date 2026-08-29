# Task 6 report — the documents

## What changed

- `docs/reference.md` (§ The two files): added the `findings:` block to the `run.yaml` shape
  (absent entirely on a clean run, one `{level, code, path, message}` entry per finding, in emission
  order), with a prose paragraph explaining redaction, the `level: error` case (`E-INPUT-CHANGED`),
  and `report`'s rendering as a `finding` row in record order.
- `docs/reference.md` (§ Exit codes and diagnostics): added a paragraph stating `run`, `draft` and
  `resume` persist their own findings via `findings:`; `validate`, `dry-run`, `report`, `freeze`,
  `diff`, `study`, `docs` and `reproduce` do not, because they write no record; and that `validate`'s
  findings are re-derivable from the byte copy of `config.yaml` a run directory holds, which is why
  the boundary falls at `run.yaml`'s write rather than earlier.
- `docs/superpowers/spec-defects.md`: removed the OPEN entry "a run-time warning is never written to
  `run.yaml`…" in full (closed by code), and appended a new recount sentence to the preamble in its
  existing idiom, netting section/OPEN counts from 152/62 to 151/61. Left the weighted-plus-clustered
  entry untouched.
- `docs/feasibility-growth-chart-literacy.md` (gap 10): corrected the closing sentence — the general
  form is closed (not filed), pointing at `reference.md`'s `findings:` block and `Collector`'s one
  redaction implementation; noted the `diff` half of the original worry was measured false during
  scoping (`diff` reads five named rows and recurses only into the covered config, never the whole
  record).

## Consistency passes

- **Mechanical**: no trailing whitespace/tabs introduced; all new/referenced anchors
  (`#the-two-files`, `#exit-codes-and-diagnostics`, `#warnings-core-reports`,
  `reference.md#the-two-files`) resolve via a script that derives GitHub-style slugs from every
  heading in the four documents plus both feasibility analyses and `spec-defects.md`, skipping fenced
  code; no duplicate anchors produced. No tables were added or resized.
- **Cross-document**: grepped README.md and `docs/design-principles.md` for `hypotheses:`/`results:`/
  `findings` — only README's partial `results:` excerpt exists and needed no change (it doesn't show
  `hypotheses`, `provenance`, or a full record, so it's not the shape `findings:` was added to).
  Grepped all four documents, `CLAUDE.md`, and both feasibility analyses for the removed
  spec-defects.md sentence and its title — zero hits.

## Spec-defects counts

Before: 152 sections, 62 `OPEN`. After: 151 sections, 61 `OPEN`.

## Disagreement with the brief

None. Task 1 (mentioned in the brief's context) was already landed per the slice history; this task
covered only the three documents as scoped.
