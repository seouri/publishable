# Task 2 review — `d05b41a..10b488d`

Reviewed by re-measuring both counts from the source, independently of the implementer's list.

## Verdicts

1. **Spec compliance: ✅**
2. **Task quality: ❌** (one Important, three Minor)

## The two counts, measured independently

**`validate.py`'s `except ContractError` guard (line 518): two codes.** Verified by tracing the
whole call tree rather than grepping one file. The only call inside the `try` is
`resolve_template` (`templates/registry.py:54`) → `_merged` (`registry.py:30`) → `discover_local`
(`templates/discovery.py`). Every `raise` reachable from there:

- `registry.py:37` — `E-TEMPLATE-COLLISION` (local name shadowing a core name).
- `discovery.py:393` — `E-TEMPLATE-COLLISION` (one name claimed twice locally).
- `discovery.py:373` (`raise load_faults[0]`), fed by four construction sites — 310 (`sys.exit()`),
  328 (raise while importing), 337 (registers nothing), 356 (non-`BaseTemplate`) — all
  `E-TEMPLATE-LOAD`.

**No third code can reach the guard**, and the decisive check is `discovery.py:319-330`: the
`except Exception` is deliberately *relabelling*, so even a template top level that raises its own
coded `ContractError` (`E-PARAM-VALUE`, say) arrives as `E-TEMPLATE-LOAD` with the original
surviving only inside `{exc!r}`. The only statement outside a per-file `try` is `drain_pending()`
(`discovery.py:63-65`), which cannot raise; `find_repo_root`'s `ContractError` is caught by a
separate guard at `validate.py:504`, outside this one. **Two — confirmed, matching the amended
comment.**

**`reference.md`'s early-return paragraph: five codes, over four `return None` statements.**
The codes, walked in `validate_config` (`validate.py:485-538`): `E-CONFIG-PARSE` (both
`load_document` sites, 476 and 480, share the code) → container-shaped `E-CONFIG-SHAPE`
(`_check_shape` returning `False`; leaf faults from `check_envelope` deliberately leave `ok`
untouched, so only container faults reach it) → `E-TEMPLATE-LOAD` and `E-TEMPLATE-COLLISION` (the
guard above) → `E-TEMPLATE-UNKNOWN` (532). **Five — confirmed.** The correspondence to `return
None` statements is *not* one-to-one: there are **four** (496, 499, 531, 538), because 531 serves
two codes. The document is right because it counts faults/codes; see Minor 1 for the report.

## Findings

**Important 1 — `reference.md`'s paragraph now contradicts itself; only `validate.py` fixed the
noun.** The task's question was not the number but *what the phrase counts*, and the two sites were
answered differently. `validate.py:519-520` changed "two today" → "two **codes**" and then spells
the distinction out ("Two *codes*, not two faults"). `reference.md` **kept the head phrase "Five
faults"** (brief Step 3: *"Keep 'Five faults'"*) and bolted a clarifier onto it, so lines 429-437
now assert all three of:

1. "**Five faults** return `validate_config` early, in this order: …"
2. "That is five ***codes***."
3. "…adds a **fault to this list** without adding a row to the table below or a **sixth to this
   count**."

These cannot all hold. If the list holds five *faults*, adding a fault to it makes six. Steelmanned
the other way — "Five faults" read as five fault-*kinds* — clause 3 is the wrong half instead: a
`Param` construction fault joins `E-TEMPLATE-LOAD`'s **shape** list, not this one. Before the
amendment "Five faults" was loose wording nothing depended on; after it, the paragraph's new
sentence makes the noun load-bearing, because it explicitly asserts that a sixth fault leaves the
count at five. **Remedy, either one word or one clause:** "Five **codes** return `validate_config`
early" (matching what `validate.py` now says), or reword clause 3 to "adds a **shape** to
`E-TEMPLATE-LOAD`". Filed as Important rather than absorbed because it is the task's primary
deliverable, and because it is plan-supplied text — the same origin as task 1's three Important
findings, which `progress.md` rules should be filed that way round ("a review finding against
brief-supplied text is a finding against me"). *Verified by* reading lines 429-438 as one paragraph
against `validate.py:519-529`.

**Minor 1 — the report's arithmetic, not the document's.** `task-2-report.md` says the five codes
match "the five distinct `return None` sites walked in `validate_config`". There are four; the
`except ContractError` clause returns once for two codes, as the report's own parenthetical
("the `except` clause's two codes") concedes. The amended sentence in `reference.md` is unaffected
— it says "five *codes*", which is what I measured — but the task existed to measure rather than
trust, so a justification that miscounts the sites is worth correcting in the record. *Verified by*
`grep -n "return None" src/publishable/validate.py` restricted to lines 485-538 and by reading the
function.

**Minor 2 — a code comment describing a check this commit does not contain.** `validate.py:523`
now asserts that "a `requires_env` mapping that is not total over `choices`" is a `Param`
construction fault. At `10b488d`, `grep -rn "requires_env" src/publishable/` returns **exactly one
hit: that comment.** `param.py` has no such keyword — `Param(requires_env=…)` raises `TypeError`
today, which does route to `E-TEMPLATE-LOAD`, but not for the stated reason. The sibling half of
the sentence (`default=None` without `nullable=True`) *is* real, at `param.py:34-35`. Plan tasks 3
and 4 build the argument and its totality check, so the claim becomes true before the branch
merges; it is Minor rather than Important only for that reason, and it is the CLAUDE.md habit "a
comment claiming a guarantee the code does not provide" in its temporal form. `reference.md`'s
matching sentence is *not* a finding — an unbuilt rule stated in the present tense is what a
normative spec is for. *Verified by* the grep above and by reading `param.py:25-55`.

**Minor 3 — one over-long line from the cosmetic reflow.** `docs/reference.md:439` is 140
characters against the file's ~95-character wrap, a byproduct of the reflow the report discloses.
Cosmetic; no rendering effect, and **outside CLAUDE.md's stated mechanical pass** (links, anchors,
duplicate anchors, table columns, whitespace/tabs/unicode) — noted, not a mechanical failure.
*Verified by* `awk` over lines 425-445.

## Checks that found nothing

- **Neighbouring prose still true.** The paragraph's later "before any of the later four returns is
  possible" counts codes on the same convention the amendment makes explicit (SHAPE, LOAD,
  COLLISION, UNKNOWN), so the insertion strengthens it rather than contradicting it. Lines 449, 452
  and 458 ("`E-TEMPLATE-LOAD` can never appear beside it") are untouched and unaffected.
- **"in this order" still holds** despite two of the five sharing one `return None`:
  `discover_local` raises `load_faults[0]` at `discovery.py:373` *before* the collision loop at 374,
  and `_merged`'s core-name shadow check runs only after `discover_local` returns — so
  LOAD-before-COLLISION is real behaviour, not just a reading order.
- **"Three shapes" agrees with every other enumeration**: `reference.md:575` (`validate`-reports
  row), `:1014` (`ContractError`-raises row), `:3421` (§ Templates), `:1640` (`requires_env`), and
  `discovery.py:249-255`. `sys.exit()` is folded into "raises while importing" at all of them,
  which is why four raise sites are three shapes.
- **New claims are all checkable.** Both added passages assert only the codes-vs-shapes
  relationship traced above; nothing authoritative rests on nothing (Minor 2 aside).
- **Mechanical pass, edited region.** Anchor `#a-credential-can-belong-to-a-parameter-value`
  resolves to the `###` heading at line 1616. No trailing whitespace, tabs, or invisible unicode
  anywhere in `reference.md`. Every table row at 464-480 carries the header's two columns. No
  fenced block touched.
- **Scope.** Three files: the two count phrases, their supporting prose, and the new report. No
  behaviour changed; `docs/reference.md` and `src/publishable/validate.py` show comment/prose hunks
  only.
- **Suite.** `uv run pytest` 1957 passed + 2 xfailed (unmoved); `ruff check` clean; `ruff format
  --check` 74 already formatted; `mypy` no issues in 42 source files.

Task 1's two rows were out of scope and were not re-reviewed.
