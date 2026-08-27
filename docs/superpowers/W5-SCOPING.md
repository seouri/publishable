# W5 scoping — the `# REQUIRED` marker `init` does not write

Read-only measurement against `main` at `392452a`, on 2026-08-27. Every probe and grep below
was run against that tree, never remembered. Spec claims and build facts are labelled
separately throughout.

Chartered by [`spec-defects.md`](spec-defects.md)'s entry *§ Templates promises a `# REQUIRED`
marker `init` does not write, and draws a consequence the code contradicts*, filed 2026-08-27 by
the end-to-end review of [the plugin tutorial](../tutorial-writing-a-plugin.md). `W1`–`W4` are the
sibling slices, all merged.

**Verdict: 5 tasks. Keep the null, add the marker, delete the consequence.** The filing costed two
opposite closures — make the code true, or make the document true — and **both are wrong as
stated**. Implementing the document's *empty value* rule would forbid `0`, `0.0`, `false` and `[]`
as values of a required parameter, which is the document's own consequence applied to the four
types it never considered. Narrowing the document to today's bare key loses the marker, which is
the only thing that tells a reader which keys they must fill — and in one measured case, the only
thing that *can*.

**What the third way costs is one line of `materialize.py`**, and it makes the load-bearing half of
the passage true while deleting only the half that was harmful.

**Baseline at `392452a`:** `uv run pytest -q` → **3475 passed, 1 skipped, 2 xfailed**, 380 s.

---

## 0. What the document says, what the code does

§ Templates, three claims and a consequence:

| Says | Measured at `392452a` |
|---|---|
| the three-states table: `Param(str)` — no `default` — *"`init` writes"* `""  # REQUIRED` | `    model: ` — a key with **no value, no marker**, and a trailing space |
| *"materialized with an empty value and a `# REQUIRED` marker, the same treatment `metadata.description` does"* | `grep -n REQUIRED src/publishable/materialize.py` → **two hits**, both the hard-coded `metadata.description` and `metadata.authors` lines |
| *"**The marker is what fails**: `validate` rejects a required parameter still holding its type's empty value"* | the key parses as YAML `null`, so the refusal is `E-PARAM-VALUE … is null, but the parameter is not nullable` |
| *"an empty string can never be a legal value for a required `str`"* | **`model: ""` validates clean** — `✓ config valid` |

Probed with one required `Param` of each type, through `materialize_config`:

```
'    req_str: '
'    req_int: '
'    req_list:                       # list of string'
'    req_float: '
'    req_bool: '
```

The mechanism is one line of `_parameters_block`: `value = "" if param.default is MISSING else
_scalar(param.default)`, and the comment comes from `param.comment()`, which knows nothing about
requiredness. The trailing space is that empty `value` with no comment to pad past it — `req_list`
escapes it only because its `item_type` supplies one.

**Nothing is broken at runtime.** A fresh config still fails `validate` until the key is filled,
which is what the passage exists to promise. Every detail of *how* is different, and the
consequence points the other way.

---

## 1. Both closures the filing costed are wrong

### Making the code true forbids legal values for four of five types

The document says *"its type's empty value"*. For `str` that is `""` and the rule is defensible —
an empty string is rarely a value anyone means. For the rest it is `0`, `0.0`, `false` and `[]`,
and a rule rejecting them makes a **required `int` that may legally be zero impossible to
declare** — an offset, a retry count, a threshold at the origin. The document draws the
consequence for `str` (*"If empty is legitimate, the parameter has a default and isn't
required"*) and never notices it has committed to it for four more types.

`Param` has five types (`str`, `int`, `float`, `bool`, `list`), so this is four of five.

### Making the document true loses the only signal a reader has

A bare `model:` says nothing. `metadata.description` carries a marker for exactly this reason, and
the passage's own argument — *"so the file `init` produced is complete and fails validation until
you fill it in, rather than being silently short a key"* — is right. Dropping the marker to match
the code keeps the file complete and makes it illegible.

**And in one measured case the marker is the only thing that can tell you.** `Param(str,
nullable=True)` with no `default` is required *and* accepts null, so `init` writes
`req_nullable: ` and `validate` **accepts it** — the config `init` produced is complete, unfilled,
and clean. Measured. No refusal can catch that one, because null is a value the parameter legally
takes; only a marker in the file can.

---

## 2. The third way: keep the null, add the marker

```python
value = "" if param.default is MISSING else _scalar(param.default)
comment = param.comment()
if param.default is MISSING:
    comment = f"REQUIRED — {comment}" if comment else "REQUIRED"
```

What `init` then writes, for the tutorial's own spec:

```yaml
  instrument:
    model:                          # REQUIRED — Instrument model identifier
    gain: 1.0                       # float > 0
```

Five things fall out of it, and the fifth is the one that makes it the right shape rather than the
cheap one:

1. **The document's load-bearing claim becomes true** — a required parameter is materialized with a
   `# REQUIRED` marker, the same treatment `metadata.description` gets, and the file fails
   `validate` until it is filled.
2. **No new error code and no new rule.** The value stays absent, so the existing
   `E-PARAM-VALUE … is null, but the parameter is not nullable` is still what fails, and
   [§ Validation](../reference.md#validation)'s row for that code — *"a value … fails its `Param`'s
   own check"* — already covers it.
3. **No legal value is forbidden.** `0`, `false`, `[]` and `""` all stay declarable, and the
   consequence about empty strings is **deleted** rather than implemented.
4. **The trailing space goes with it**, in every case rather than only where a constraint happened
   to supply a comment — the marker is always a comment.
5. **The marker is what distinguishes the two null-looking lines.** A nullable parameter defaulted
   to `null` renders `thing: null`; a required one renders `model:` with the marker. § 1's
   unfillable-but-clean case becomes visible to a reader in the one place it can be.

The format follows `metadata`'s exactly — `# REQUIRED — <text>` where there is text, `# REQUIRED`
alone where there is not — and `comment()` already answers *which single thing claims the line*, so
the marker prepends rather than competes.

---

## 3. What is unpinned, which is why this drifted

`grep -rc "REQUIRED" tests/*.py` → **22 lines across six files**, and **not one pins `init`'s
rendering of a required parameter.** Attributed individually rather than counted: twelve in
`test_validate.py` are `E-META-REQUIRED`, `E-DATA-REQUIRED`, `E-ENTRYPOINT-REQUIRED`, a
`_REQUIRED_ENV_TEMPLATE` fixture name and § The one config file's `assign` row; three in
`test_study.py` are `E-STUDY-CONFIRM-REQUIRED`; two in `test_artifacts.py` are
`E-STEP-READ-REPEAT-REQUIRED`; two in `test_diagnostics.py` are `E-META-REQUIRED` in a rendering
fixture; one in `test_cli.py` is *"Fills the two REQUIRED"* (metadata); and two in
`test_reproduce.py` pin a **different** artifact's marker
(`  {key}: ""   # REQUIRED: set to your local copy`, a third format again).

**That count was first written as "six", off a `head -8` of the grep** — the truncated output read
as the whole of it. Recorded rather than quietly fixed, because a number offered as verification
evidence has to be the number the command printed, and this one was not. The conclusion survives
the correction: twelve hits nobody had read turned out to be six other error codes.

So the surface the document describes in a table, a paragraph and a consequence has no test at all.
That is the whole reason four slices of review passed over it, and it is why task 2 is a pin rather
than a probe.

---

## 4. Decomposition — 5 tasks

1. **`_parameters_block` prepends the marker.** Three lines, and the trailing space goes with it.
2. **The pin.** One arm over all five types — required with help, required with a constraint,
   required with neither — asserting the marker, the absent value and **no trailing whitespace**;
   one arm asserting a fresh config fails `validate` with `E-PARAM-VALUE` on that path; one arm
   asserting a **defaulted** parameter's line is unchanged, which is the control that stops the
   marker leaking onto every line.
3. **§ Templates: the table cell and the paragraph.** The cell stops promising `""` and says what
   the line is; the paragraph keeps *"the same treatment `metadata.description` does"* and loses
   *"an empty value"*. The *"marker is what fails"* sentence and the empty-string consequence are
   **deleted** — what fails is the absent value, and `""` is legal. Deletion rather than rewriting:
   the consequence was reasoning from a mechanism that was never there.
4. **The nullable-required case gets its sentence** where the three states are described, because
   `validate` cannot catch it and § 1 shows the marker is the only signal. One sentence, not a
   refusal — a `Param(str, nullable=True)` with no default is a coherent declaration and forbidding
   it would be a second slice's argument.
5. **The sweep and the filings.** Every `REQUIRED` hit in the four documents attributed
   individually: `reference.md:68`/`:69` are `metadata`'s real output and stay; `:98` is § The one
   config file's schema fence, wider than `init`'s output by its own statement, and stays; `:4290`
   is `reproduce`'s own artifact and stays; `:1908` and `:1912` are task 3's. Then the tutorial's
   three, which **flip from describing a defect to describing the behaviour**, and the
   `spec-defects.md` entry struck.

---

## 5. What is NOT in this slice

- **Rejecting `""` for a required `str`.** § 1: it is the document's rule generalized, and it
  forbids `0`/`false`/`[]` for the other four types. The consequence is deleted instead.
- **Refusing `Param(type, nullable=True)` with no default.** § 1's unfillable-but-clean case. It is
  a coherent declaration — *you must decide, and null is a decision you may make* — so it is
  disclosed rather than refused, and refusing it is an argument a later slice can make.
- **Unifying the three marker formats.** `metadata`'s `# REQUIRED — …`, `reproduce`'s
  `# REQUIRED: …`, and the marker this slice adds. This slice matches `metadata`, which is the one
  it is documented against; `reproduce`'s is a different artifact written by a different command and
  pinned by its own test.
- **§ The one config file's fenced schema.** `generic` declares no required parameter — every one of
  its four `Param`s carries a default — so no shipped example, no worked config and no
  `parameters_hash` in any document moves. Verified before this slice was scoped, and it is why a
  change to `init`'s output costs nothing here.
