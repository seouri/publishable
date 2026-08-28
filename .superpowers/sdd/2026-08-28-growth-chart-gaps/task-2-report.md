# Task 2 & Task 3 — report

## Task 2 — `fold` level's `stratify_by` type

`docs/reference.md` § Repeat kinds, the per-kind field table, the `fold` row (previously line 2174):
added the type `str | None`, stated it names **one** attribute (a fold balances its folds on a
single attribute), and named the two sibling spellings that are lists —
`holdout.stratify_by` and `assign.<axis>.stratify_by` — linking to their own sections
(`#a-fixed-holdout-split`, `#allocation-within-subjects-or-between-subjects`).

Verified against `src/publishable/replication.py:49` (`stratify_by: str | None = None`).

**E-REPL-FOLD-STRATIFY-UNKNOWN row check** (§ Errors `validate` reports, the row ending in that
code): it already says a `fold` level's `stratify_by` is reported here when it names an unknown
attribute or "is not the name of an attribute at all — a non-string, an empty string, or an empty
list," and explains the non-string case is caught here (not `E-CONFIG-TYPE`) specifically *because*
`stratify_by: [label]` — the **list form** `holdout`, `assign`, and `resample` each take — would
otherwise escape every check. That row already states the fold/holdout/assign asymmetry the new
table-cell sentence echoes; my edit does not contradict it, and the two are now consistent from
both directions (the field table states the type and the asymmetry, the error row explains why the
asymmetry matters for validation).

## Task 3 — what `measurements.collapse` applies to

`docs/reference.md` § The one config file, in the paragraph beneath the `measurements` inline
comment that names `by` and `collapse` (part of the large paragraph following the fenced config
example): added a sentence stating `collapse` applies to **every** column the resolved unit
carries, not only ones the config names — the bare rule form applies to all columns alike, and a
per-column map is the ordinary way to vary it per column (falling back to `first` for an unnamed
column), rather than an exception. Pointed at § Validation's *Collapse rule fits the column* row
for what a mismatched rule earns, without restating that row's contents.

Verified against `src/publishable/units.py` — `rule_for()` (around line 857): a per-column map
falls back to `("first")` for any column not in the map, confirming every carried column receives
a rule (map entry or fallback), not only ones the config explicitly names. `COLLAPSE_RULES` /
`NUMERIC_COLLAPSE_RULES` constants sit just above it.

## Mechanical pass

Ran a throwaway Python script over `docs/reference.md` (skipping fenced code blocks for
structural checks):

- Trailing whitespace / tabs: none found.
- Table row column counts (unescaped pipes only, `\|` in a cell excluded): every row matches its
  header's column count; no empty rows.
- Heading→anchor duplicate check (GitHub-slugger-accurate: strip non-word/space/hyphen chars,
  replace **each** space with a hyphen individually — not collapsed — which is why headings like
  `` `identity.json` — the claims... `` correctly slug to a double hyphen): no duplicate anchors.
- Every `](#anchor)` link in the file resolves against the heading-derived anchor set, including
  both anchors newly added in Task 2's edit (`#a-fixed-holdout-split`,
  `#allocation-within-subjects-or-between-subjects`) and the pre-existing `#validation` link
  reused in Task 3's edit.

First slugger pass (naive `\s+` → single `-` collapse) produced ~29 false-positive "broken" links
against headings like `` `identity.json` — the claims... ``; fixed by replacing each space
individually instead of collapsing runs, which is GitHub's actual slugify behavior. All of those
were pre-existing headings/links, unrelated to either edit — confirmed no new breakage from this
session's two edits specifically.

## Diff summary

Two single-cell/sentence insertions in `docs/reference.md`, no line-count/numbering changes to any
table or list elsewhere in the file, no code changes.
