# H5a tasks 3–4 — report

Commits: `a2b6b51` (task 3), `8822dc9` (task 4).

Test summary: full suite green at both commits, unchanged from the batch's stated baseline —
**2845 passed, 1 skipped, 2 xfailed** — since both tasks are documents-only. All four gates
(`ruff check .`, `ruff format --check .`, `mypy`, `pytest`) clean at both commits.

## Task 3 — three § Errors rows widened to every emit site

**Enumerated by reading first, then confirmed by grep, in that order** (the reverse order is the
substitution named in the brief as the cause of H7c's credential leak).

- **`E-STEP-RETURN-TYPE` — three sites**, all read directly before grepping:
  - `src/publishable/coercion.py:226`, `_refuse` (called from `_coerce_one`) — a value core can't
    coerce to a scalar. Reached from `io.record`'s values, a step's `run` return
    (`coerce_scalars` call in `runner.py`), and a template's `aggregate` return.
  - `src/publishable/runner.py:783` — a step's `run` returning anything but a mapping or `None`,
    checked with `isinstance(returned, dict)` before `coerce_scalars` ever runs.
  - `src/publishable/artifacts.py:118`, inside `_check_column_types`, called only from
    `_encode_parquet` (confirmed: `_encode_csv` has no such call) — a `.parquet` row set whose
    rows disagree on a column's type once coerced. Grep (`grep -rn 'E-STEP-RETURN-TYPE' src/`)
    turned up exactly these three `raise`/`_refuse` sites and no fourth, matching the brief's
    claim that the scoping's two-site read missed `runner.py`.
  - Widened row (§ Errors core raises) states all three, and states the `.parquet`-only scope of
    the cross-row disagreement check explicitly, consistent with the already-shipped § The
    per-unit tables sentence ("`.csv` write does not unify a column's types across rows at all
    today") from task 1. **This row also states a `.csv` row's own cell as a fourth clause** —
    a written `.csv` cell that isn't a scalar core can coerce to one — which is Decision 5 as
    narrowed by the design's *second* controller ruling (`.csv` refuses a structural/`bytes`
    cell because it cannot round-trip one; `.parquet` does not, because it can). **This code does
    not exist yet** (task 9); per the brief's documents-lead order this is deliberate, but it
    means task 9's reviewer must re-read this row against the code it lands, specifically to
    confirm the refusal is `.csv`-only and that `.parquet` gained no matching refusal.
- **`E-STEP-KEY-COLLISION` — sites in `artifacts.py` and `stats.py`**, read directly:
  - `artifacts.py:649/681` — a recorded column named `unit` (both the `measurement=` branch and
    the plain branch check this today).
  - `artifacts.py:655` — a recorded column named `measurement` (only the `measurement=` branch
    checks this today; the brief scopes today's widening to Decisions 5/8 only, not Decision 9's
    later symmetric fix in the plain branch, so the row does not claim that symmetry).
  - `artifacts.py:663/689` — a recorded column shadowing a declared unit attribute (both
    branches).
  - `stats.py:3115` — a derived key against the reserved metric name `by` (already documented
    separately, in § Steps and artifacts' "One metric name is reserved: `by`" paragraph, and
    cross-referenced from there — not duplicated into this row, per the brief's specific list of
    what to add).
  - `stats.py:3123` — a derived key against a recorded column.
  - Widened row adds the `unit`/`measurement` structural-column clauses the brief named; left the
    existing "derived key against a recorded column, a recorded column against a unit attribute"
    clause as-is.
- **`E-ARTIFACT-UNWRITABLE` — one site today** (`artifacts.py:844`, `StepIO.write`'s `else`
  branch for an unregistered suffix handed a non-`bytes`/non-`str` object), confirmed by grep
  (`E-ARTIFACT-UNWRITABLE` appears at exactly one `raise` and in the shared § Errors row's own
  prose). Widened row adds the non-mapping-row clause task 9 will build; **this code does not
  exist yet either** — same documents-lead caveat as above.
- **Verified the untouched count phrase**: "Four emit sites for the escape alone" (the
  `E-ARTIFACT-NAME` clause in the same shared row) — re-derived by grep
  (`grep -rn 'E-ARTIFACT-NAME' src/`), which returns exactly four `_contained(..., code=
  "E-ARTIFACT-NAME")` call sites: `artifacts.py:819` (`StepIO`'s own write), `:908`
  (`StepIO.read_condition`), `:964` (`StepIO.read_upstream`), `:1193`
  (`ReportIO.read_condition`). Untouched, confirmed still accurate.

**What the widening does not license, stated as the brief requires**: the `.csv`-cell clause on
`E-STEP-RETURN-TYPE` and the non-mapping-row clause on `E-ARTIFACT-UNWRITABLE` both describe code
task 9 has not written. Task 9's reviewer must re-read both rows against the code once it lands,
in particular to confirm the second controller ruling's `.parquet`-accepts/`.csv`-refuses split
survived into the implementation and that no `.parquet` refusal appears for a structural or
`bytes` cell.

## Task 4 — mint `E-UNITS-ATTR-COLUMN`, before any code raises it

Three homes, per the brief and per Correction 10/11 (the `unit`-shadow filing's prediction that
the fix "touches § Errors core raises" is wrong — confirmed by reading: `E-UNITS-ATTR-RESERVED`
appears only in § Validation and § Errors `validate` reports, never in § Errors core raises,
because `validate` is what reports it):

- **§ Validation**'s *Attribute names aren't reserved* row now names both cases inline
  (parenthetical codes, matching the existing house style at line 314/319's own rows), sending a
  reader holding either code to the right fault.
- **§ Errors `validate` reports** gains a new row directly beside `E-UNITS-ATTR-RESERVED`,
  stating the lifetime ground for two codes rather than one wider row (permanent `Unit`-field
  names vs. revocable column/block names), cross-referencing `E-APPARATUS-FACT-TYPE`'s row for
  the "sharing a mechanism is not sharing a fault" principle the brief named, and stating
  **one emit path, not two surfaces** per Correction 10: `command_run` calls `validate_config`
  first and returns before its own `resolve_units` call, so `run` meets this refusal only through
  `validate`'s gate, for every source (table, glob, resolver) — never a second, dual-surface
  check the way `E-UNITS-ATTR-MISSING`/`E-RESOLVER-YIELD` are. No row claims a raise site that
  does not exist: task 4 mints an identifier and documents a validate-time finding; the code that
  makes it fire (task 5) is not built yet, and the row makes no claim about a raise site in
  § Errors core raises.
- **§ Steps and artifacts** gains a new paragraph after the existing "One metric name is
  reserved: `by`" one, distinguishing the two namespaces without re-arguing the metric sentence
  (grepped "set of one" — the only hit is the pre-existing sentence, confirmed unedited and still
  true: the metric set stays `{by}`). States stoppage 3 with what ran before (a declared
  attribute named `unit` replaced the unit-key column, publishing `[{'unit': 'HIJACK', ...}]`)
  and what happens now (refused at `validate`, so a `run` stops at the same gate before its first
  execution). States explicitly that the refusal removes one *producer* of a `by` column, not
  the *possibility* of one — a step recording `by` stays legal — so a recorded `by` column still
  has to be told apart from a metric by where it sits, never by name.
- **`docs/experimental-designs.md` § Mistakes core prevents**: decided to add a row (Bookkeeping
  category), since the fault is now structurally impossible in the schema (refused at `validate`)
  rather than merely discouraged, satisfying the section's own admission criterion. Checked the
  insertion moved no count phrase or positional locator near it (grepped the table and its
  neighbors; none exists).

**Mechanical pass on both files**: anchors used (`#the-per-unit-tables`, `#reporting-strata`,
`#errors-validate-reports`, `#errors-core-raises`, `#where-units-come-from`) all resolve to real
headings, checked with a slug-computing script over both files; no trailing whitespace/tabs; all
edited rows are single-line two-column table rows with matching pipe counts. The script's
anchor check independently flagged several **pre-existing** `&`-containing anchors as
false positives (e.g. `#secrets--credentials`) — confirmed unrelated to this diff (none of my
new links appear in that list) and not touched.

## A genuine ambiguity I resolved by reasoning, not by copying either source verbatim

The brief and plan's task 3 step 2 read: *"a written `.csv` or `.parquet` row whose value is not
a scalar or whose rows disagree on a column's type."* Read literally, this could imply **both**
formats refuse a non-scalar cell. That contradicts the design's second controller ruling, which
is unambiguous and later than the plan text: `.parquet` round-trips a structural/`bytes` cell
intact and gains no refusal; only `.csv` does. I read the brief's sentence as binding each clause
to one format (`.csv` → non-scalar value; `.parquet` → cross-row disagreement), which is the only
reading consistent with the second ruling, with Correction 8, and with task 9's own plan (mutation
(ii) targets `_encode_csv` only for the structural-cell case). I did not find a plan or design
passage that states this binding as explicitly for the first clause as it does for the second —
flagging it here rather than silently picking a side, since task 9's implementer should verify
this reading against whatever code Decision 5 (as narrowed) actually produces.

## Concerns for review

1. The § Errors core raises rows for `E-STEP-RETURN-TYPE` and `E-ARTIFACT-UNWRITABLE` describe two
   clauses (the `.csv`-cell refusal, the non-mapping-row refusal) that task 9 has not built. This
   is the documents-lead order the brief calls for, but it means these two clauses are unverified
   against code and must be re-read once task 9 lands.
2. The ambiguity resolved above (the `.csv`/`.parquet` format binding in task 3's own brief text)
   is worth the controller's attention — if my reading is wrong, the § Errors row I wrote needs a
   correction once task 9's actual code is in hand.
