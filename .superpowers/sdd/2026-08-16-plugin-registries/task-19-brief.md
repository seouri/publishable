## Task 19: Decision 4 — envelope closure of `data.units.from`, and the mutual exclusion

**Files:** Modify `src/publishable/envelope.py`, `src/publishable/validate.py`,
`docs/reference.md`, `tests/test_envelope.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `envelope.LEAF_TYPES`, an ordered dict whose entry `"data.units.from": (str, dict)` stops
  at the mapping; `envelope._known_containers()`, which derives every dotted prefix a `LEAF_TYPES`
  path implies, and the three module constants computed from it at import — `_KNOWN_LEAVES`,
  `_KNOWN_CONTAINERS`, `_KNOWN_OR_EXEMPT`; `envelope._check_unknown_keys`, which checks **containers
  before leaves** so a path that is both is descended into; `envelope.check_envelope`'s type loop,
  which walks a dotted path and stops at the first non-mapping node;
  `validate._check_unimplemented`'s resolver emit, which reads
  `units.get("from")` and reports `E-DATA-RESOLVER-UNSUPPORTED` when `"resolver" in source`;
  `units.resolve_units`, which branches `str` → table, `{glob: …}` → glob, else raise
  `E-UNITS-SOURCE-MISSING`.
- Produces: `LEAF_TYPES` entries `"data.units.from.glob": str` and `"data.units.from.resolver": str`;
  `validate._check_units_source(doc, c) -> None` emitting `E-UNITS-SOURCE-AMBIGUOUS`; two false
  comments in `envelope.py` deleted.

**The two faults, both measured rather than reasoned.** Probed at `ff51864` against a real scaffolded
project with the closure applied in-process and one field mutated at a time:

```
from: index.csv                      → []
from: {glob: "*.csv"}                → []
from: {resolver: x}                  → ['E-DATA-RESOLVER-UNSUPPORTED']
from: {resolverr: x}                 → ['E-CONFIG-KEY-UNKNOWN', 'E-UNITS-SOURCE-MISSING']
from: {glob: "*.csv", resolver: x}   → ['E-DATA-RESOLVER-UNSUPPORTED']
from: {resolver: 123}                → ['E-CONFIG-TYPE', 'E-DATA-RESOLVER-UNSUPPORTED']
```

The `E-CONFIG-KEY-UNKNOWN` message carries `did you mean \`resolver\`?`, which is the closure's
`difflib` hint working. **Both new codes on the misspelling row come from the closure and from
`resolve_units` respectively, and `validate` collects, which is why both appear** — do not write a
test asserting one of them alone.

**The both-keys fault, and why it is minted now.** `_check_unimplemented` branches on
`"resolver" in source` and `_check_units` skips on the same test, so `validate` calls a
both-keys mapping a resolver; `resolve_units` branches on `"glob" in source` **first**, so a run
would call it a glob. Two answers to one declaration. It is unreachable today because the refusal
stands, and **reachable the moment Part B's dispatch lands** — so the refusal belongs in the slice
that closes the envelope, not the one that opens the path.

**Where the check lives, and why not in `_check_unimplemented`.** Its own function, called from
`validate_config` immediately before `_check_units`. Not in `_check_unimplemented`, whose resolver
entry Part B task 24 deletes — a sibling emit inside that block would be deleted with it, and this
refusal is permanent. Not in `_check_data`, which returns early when there is no git repo.

**Names already at module level in `tests/test_envelope.py`:** read them before adding anything.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_envelope.py` a check on the closure
      itself, using whatever that file's established way of calling `check_envelope` is:

```python
def test_a_misspelled_from_key_is_reported_rather_than_ignored():
    """The closure's whole purpose. `envelope.py`'s own module docstring claimed
    this key was "reported by no check in this build", which was false even
    before the closure — `resolve_units` reported it as a missing source — and is
    now false twice over, with a `difflib` hint naming the key meant."""
    findings = check_envelope({"data": {"units": {"from": {"resolverr": "x"}}}})
    codes = {code for code, _, _ in findings}
    assert "E-CONFIG-KEY-UNKNOWN" in codes
    message = next(m for code, _, m in findings if code == "E-CONFIG-KEY-UNKNOWN")
    assert "did you mean `resolver`?" in message

    # THE CONTROL: both spelled keys, and the string form, report nothing here —
    # so the check above is about an unknown key rather than about descending
    # into `from` at all.
    assert check_envelope({"data": {"units": {"from": {"resolver": "x"}}}}) == []
    assert check_envelope({"data": {"units": {"from": {"glob": "*.dcm"}}}}) == []
    assert check_envelope({"data": {"units": {"from": "index.csv"}}}) == []


def test_a_wrongly_typed_from_child_is_a_type_finding():
    findings = check_envelope({"data": {"units": {"from": {"resolver": 123}}}})
    assert [(code, path) for code, path, _ in findings] == [
        ("E-CONFIG-TYPE", "data.units.from.resolver")
    ]
```

      and to `tests/test_validate.py`:

```python
def test_a_from_mapping_declaring_both_glob_and_resolver_is_refused(write_config):
    """Two answers to one declaration: `validate` reads it as a resolver
    (`_check_unimplemented` tests `resolver in source`) and `resolve_units` would
    read it as a glob (it tests `glob` first). Unreachable while the wholesale
    refusal stands and reachable the moment dispatch lands, so the refusal is
    minted in the slice that closes the envelope.

    Asserted ALONGSIDE the wholesale refusal, never instead of it, and never on
    the whole code set — Part B deletes one line here.
    """
    found = messages_by_code(
        write_config({"data.units.from": {"glob": "*.csv", "resolver": "plate_wells"}})
    )
    message = found["E-UNITS-SOURCE-AMBIGUOUS"]
    assert "glob" in message
    assert "resolver" in message
    assert "E-DATA-RESOLVER-UNSUPPORTED" in found

    # THE CONTROLS, both produced by the code under test: either key alone is not
    # ambiguous. Without these, a check that fired for any mapping would pass.
    assert "E-UNITS-SOURCE-AMBIGUOUS" not in codes(
        write_config({"data.units.from": {"glob": "*.csv"}})
    )
    resolver_only = codes(write_config({"data.units.from": {"resolver": "plate_wells"}}))
    assert "E-UNITS-SOURCE-AMBIGUOUS" not in resolver_only
    assert "E-DATA-RESOLVER-UNSUPPORTED" in resolver_only
```

- [ ] **Step 2: Run and see them fail.** The envelope tests report no `E-CONFIG-KEY-UNKNOWN` and no
      `E-CONFIG-TYPE`; the validate test fails on `KeyError: 'E-UNITS-SOURCE-AMBIGUOUS'`.

- [ ] **Step 3: Implement the closure.** In `src/publishable/envelope.py`, add two entries
      immediately after `"data.units.from": (str, dict),`:

```python
    # Closed one level in, the arrangement `data.units.measurements` and
    # `.holdout` already have: the two keys a `from` mapping may carry are fixed,
    # so leaving the block whole makes a typo among them unreachable by any check
    # — which is what a `resolverr` was until this closure, reported only as a
    # missing source and never as a misspelled key. Closed here **before** the
    # resolver's own wholesale refusal retires, the same order `resample` took:
    # the shape is checked before the values are honoured.
    "data.units.from.glob": str,
    "data.units.from.resolver": str,
```

      **Nothing else changes.** `_KNOWN_LEAVES`, `_KNOWN_CONTAINERS` and `_KNOWN_OR_EXEMPT` are
      derived at import from `LEAF_TYPES`, so both the container closure and the `difflib` hint pick
      the entries up for free; `_check_unknown_keys` checks containers before leaves, so
      `data.units.from` — now both — is descended into rather than stopped at; and
      `check_envelope`'s type loop stops at a non-mapping node, so a string `from` still types
      cleanly against `(str, dict)` and reaches neither new entry. **Verify each of those three by
      running the tests rather than by reading**, since all three are properties of code this task
      does not touch.

- [ ] **Step 4: Implement the mutual exclusion.** In `src/publishable/validate.py`:

```python
def _check_units_source(doc: dict[str, Any], c: Collector) -> None:
    """A `data.units.from` mapping may declare `glob` or `resolver`, not both.

    Two answers to one declaration: this module reads such a mapping as a
    resolver — `_check_unimplemented` and `_check_units` both test for the
    `resolver` key — while `units.resolve_units` tests for `glob` first and would
    resolve it as a glob. Whichever is right, they cannot both be, and a run that
    executed one while `validate` had checked the other is the fault this refuses.

    Its own function rather than a branch beside the resolver refusal, because
    that refusal retires and this one does not: a `from` naming two sources is
    ambiguous whether or not resolvers are honoured.
    """
    units = _units_declaration(doc.get("data") or {}, c) or {}
    source = units.get("from")
    if isinstance(source, dict) and "glob" in source and "resolver" in source:
        c.error(
            "E-UNITS-SOURCE-AMBIGUOUS",
            "data.units.from",
            "declares both `glob` and `resolver`, which name two different ways of "
            "finding the same roster — `from` says how core finds a unit, and a "
            "declaration with two answers has none. Declare one",
        )
```

      Call it from `validate_config` immediately before `_check_units`, which is the check that
      resolves the roster this declaration decides the shape of.

- [ ] **Step 5: Delete `envelope.py`'s two false comments.** In the module docstring, the sentence
      "a misspelled `resolverr` in a `data.units.from` mapping is reported by no check in this
      build" is false and its subject is now closed — **delete the clause** and let the surrounding
      argument about whole leaves stand on `measurements`' and `holdout`'s example, which it already
      does. In `_check_unknown_keys`' docstring, "a `from` dict's `resolver` is reached by no check
      in this build: not here, and not by `_check_shape`, which checks a container's shape and never
      the names inside one" is false in both halves — `_check_unimplemented` reads it, and now this
      closure does. **Delete that clause too**, keeping the sentence's general rule about not
      descending into a known leaf "unless the table also declares paths BENEATH it", which is
      exactly what these two new entries are and is the mechanism a reader needs.

      Preferring deletion to rewriting is the rule here: a round in this repo closed a false-claim
      finding by propagating the claim to two more sites.

- [ ] **Step 6: Document it.** Add a row to § Errors `validate` reports, beside the row reporting a
      `data.units.from` that names no usable source — name that sibling by what it does:

```
| [`data.units.from`](#where-units-come-from) is a mapping declaring **both** `glob` and `resolver`. `from` answers one question — how core finds a unit — and a declaration with two answers has none: one form builds the table from matching paths and the other hands the work to a plugin, and they resolve different rosters. Refused rather than ordered, for the reason every collision in this document is: a rule for which key wins would be a rule nobody could read off the config | `E-UNITS-SOURCE-AMBIGUOUS` |
```

      And in § Validation, add a row beside the check that reports **where units come from**:

```
| One source per roster | `data.units.from` declares `{glob: "*.dcm", resolver: plate_wells}`; the two find different units |
```

- [ ] **Step 7: Run and see them pass**, then the whole suite. **`tests/test_envelope.py` in full is
      the regression surface** — the closure changes what `_known_containers()` derives, so any test
      asserting on the set of known containers or on `_immediate_children` moves. Run that file
      first and read every failure; a failure there is a real consequence to be understood, not a
      fixture to be edited. Expected: predecessor's count **+ 3**.

- [ ] **Step 8: Mutate — three.**

  **(a) Remove one closure entry.** Delete `"data.units.from.glob": str`.
  `test_a_misspelled_from_key_is_reported_rather_than_ignored` must still pass — `resolverr` is
  still unknown — but its **control** `check_envelope({"data": {"units": {"from": {"glob": "*.dcm"}}}}) == []`
  must FAIL, since `glob` becomes an unknown key. **Checked against the body:** the control asserts
  the empty list for both spelled keys, so removing either entry reddens it. **This is the mutation
  that proves both entries are wired**, and the misspelling assertion alone does not.

  **(b) Require only one key for the ambiguity.** Change the condition to
  `"glob" in source or "resolver" in source`. `test_a_from_mapping_declaring_both_glob_and_resolver_is_refused`
  must FAIL on its **first control** (`glob` alone). **Checked against the body:** the test declares
  each key alone as well as both, which is the only arrangement in which the two readings differ; a
  test asserting only the both-keys case would pass under this mutant.

  **(c) Report instead of alongside.** In `_check_unimplemented`, guard the resolver emit with
  `and "glob" not in source`. `test_a_from_mapping_declaring_both_glob_and_resolver_is_refused` must
  FAIL on `assert "E-DATA-RESOLVER-UNSUPPORTED" in found`. **This is the mutation that pins the
  alongside-never-instead-of discipline**, and it is the one that would go quiet if a future task
  wrote the test against a total code set instead.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches.** **The two deleted comments are unpinned** —
      nothing reads a docstring — and **nothing closes that**; the verification is that the claims
      they made are now demonstrably false, which step 1's tests show. **`_check_units_source`'s
      finding path (`data.units.from`)** is unpinned as every path in this slice is.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: data.units.from is closed one level in, and a mapping naming two sources is refused`

---

