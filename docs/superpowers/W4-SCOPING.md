# W4 scoping — `Config.raw`'s missing reader

Read-only measurement against `main` at `50d1a8a`, on 2026-08-27. Every grep and probe below
was run against that tree, never remembered. Spec claims and build facts are labelled
separately throughout.

Chartered by [`spec-defects.md`](spec-defects.md)'s entry *`Config.raw` has no reader in core's
own source*, filed by [`W2-SCOPING.md`](W2-SCOPING.md) § 0.3 on 2026-08-27. `W1`, `W2` and `W3`
are the sibling slices, all merged.

**Verdict: 4 tasks, the accessor stays, and the filing measured the wrong thing.** *No reader in
`src/`* is the right test for a **declaration core is supposed to read** — `required_env`,
`apparatus_probe`, `field_convention`, every example CLAUDE.md's own row has ever carried. `raw`
runs the other way: it is an accessor **user code** calls, and core neither needs nor should have
a call to it. Applying the row to it inverts the arrow.

The real gap is next door and is what this slice closes: **`raw` appears in no example in any
document.** A public accessor with a real use, documented only by a sentence saying it exists, is
how a surface ends up looking unread.

**Baseline at `50d1a8a`:** `uv run pytest -q` → **3473 passed, 1 skipped, 2 xfailed**, 360 s.

---

## 0. Three measurements

### 1. The use is real, and `raw` is the only route to it

A step's `cfg` is dot-access with no methods, and a **nested** node carries no `raw`
(`cfg.parameters.raw` → `E-STEP-PARAM-UNKNOWN`, measured). So `cfg.raw["parameters"]` is the only
way a step can obtain its own parameters as a mapping. Probed through the real `StepIO`:

```
--- a node handed to io.write('.json') ---
TypeError: Object of type Node is not JSON serializable
--- cfg.raw['parameters'] handed to io.write('.json') ---
wrote: {"analysis": {"method": "pearson", "min_samples": 30}}
--- json.dumps on a node ---
TypeError: Object of type Node is not JSON serializable
```

So a step that wants to record what it ran under — `io.write("params.json", …)`, a `**kwargs`
splat, a `DataFrame` row — **cannot** do it without `raw`. That is not a plausible need argued
from the shape of the API, which is what the filing said it had; it is a measured one.

### 2. Nothing anywhere shows it being used

`grep -rn "cfg\.raw\|config\.raw\|\.raw\b" docs/*.md README.md` → **nothing**. § The importable
surface *describes* the accessor in two paragraphs and no example in any of the four documents,
the tutorial or the feasibility analysis calls it. The feasibility analysis's own step code reads
`cfg.parameters.llm`, `cfg.parameters.report.metrics`, `cfg.parameters.pricing.prompt_per_mtok` —
dot-access throughout, and it passes a **node** into a plugin's own `connect(cfg.parameters.llm)`,
which works because the receiver uses dot-access too.

That is the honest description of the gap: not an accessor nobody reads, but one nobody was
**shown how to read**.

### 3. Core genuinely does not need one, measured rather than assumed

`parameters_hash` is declared `parameters_hash(config: dict[str, Any])` and every call site in `src/`
passes a mapping read from a file — `cli.py:3050`, `freeze.py:240` and `:246`, `reproduce.py:868`,
`:896` and `:897`. `resolve_condition_cfg(base: dict,
condition) -> Config` takes the mapping and returns the node, so the conversion core needs runs in
the other direction. Nothing in `src/` reaches `_data` privately either — the only `_data` hits
outside `config.py` are `units.py`'s own unrelated slot.

The ten test uses (`tests/test_runner.py`) are core comparing two resolved conditions
(`resolved[0].raw == resolved[2].raw`, `parameters_hash(resolved[0].raw)`), which is a legitimate
use of a public accessor by a test and not evidence about production.

---

## 1. Why the accessor stays

- **The arrow points outward.** Every example in CLAUDE.md's *unbuilt reader of a shipped surface*
  row is core failing to read something a user declares. `raw` is core offering something a user
  calls. A surface with no core caller is the normal state for `Unit`, `Estimate`, `Param` and
  `BaseStep` too; what would be abnormal is a **user-facing** surface with no documented use, and
  that is precisely the defect here.
- **It has a use nothing else covers** (§ 0.1), and the alternative is that a step cannot write its
  own parameters to an artifact at all.
- **It is published.** `publishable` 0.1.2 is on PyPI, so removing a documented public accessor is a
  breaking change for users this repository cannot enumerate, requiring a version bump and a
  release note — spent on a surface that measures useful. W2 declined the removal because a
  documentation slice may not change a shipped surface; this slice declines it on the merits.
- **Its cost is one name**, already disclosed: a top-level config key called `raw` is unreachable
  through dot-access, and § The importable surface says so.

---

## 2. Two findings this measurement turned up

### `raw` is a shallow copy, so it is a route around the config's own immutability

`Config.raw` returns `dict(self._data)`. Measured:

```
cfg.raw["parameters"] = {...}                                  → the config still sees the original
cfg.raw["parameters"]["analysis"]["method"] = "kendall"        → cfg.parameters.analysis.method == "kendall"
                                                                 and the underlying document changed too
```

Rebinding a top-level key is harmless; mutating **inside** one is not. `Node.__setattr__` refuses a
write with `E-CONFIG-IMMUTABLE` and the reason *"The config is the record of what ran; change it in the
file"* — and this route sticks, so a step could change what a later scope reads after
`parameters_hash` was computed from the file.

**Filed rather than fixed here, and the reason is a pin.** The obvious fix — deep-copy in `raw` —
**silently defuses a shipped test**: `tests/test_runner.py::test_per_condition_cfgs_are_not_the_same_object`
asserts `cfg0.raw["parameters"]["analysis"] is not cfg1.raw["parameters"]["analysis"]` to prove
*the resolver* deep-copies per condition, and its docstring says *"that aliasing is exactly how an
earlier defect in this project first showed itself."* If `raw` copies, that assertion passes whatever
the resolver does. So the closure owes a re-expression of the resolver's claim that does not observe it
through `raw`, and a slice that copied without noticing would weaken a pin to close a defect — the
shape this repository names *a pin weakened quietly*.

### A node handed to a writer is a bare traceback, which belongs to an existing entry

`io.write("x.json", cfg.parameters)` — handing a node where a mapping was meant, the exact mistake
a reader of § The importable surface might make — raises a **bare `TypeError`**, not a coded
diagnostic. That is one more instance of
[*three writers raise a bare traceback instead of a diagnostic*](spec-defects.md),
whose measured cases are NumPy scalars nested in a mapping; the class is *any object `json` cannot
encode*. **Appended to that entry rather than filed as a new one** — before filing a "new" gap,
grep for one that exists — and out of scope here, because coding that refusal is the write-side
slice's work and not a documentation fix.

---

## 3. Decomposition — 3 tasks

1. **§ The importable surface gains the worked use.** One fenced line in the `raw` paragraph —
   `io.write("params.json", cfg.raw["parameters"])` — plus the two facts that make it the only
   route: a node is not JSON-serializable, and a nested node carries no `raw`. This is the whole
   fix: the accessor's justification stops resting on a caller list and starts resting on a use
   anybody can copy.
2. **§ Using them in step code gains the same line where a step author is reading.** § The
   importable surface is the enumeration; the step section is where someone writing a step looks,
   and the two already cross-reference. One sentence, not a second copy of the argument.
3. **The pin.** A fixture writing `cfg.raw["parameters"]` through `io.write(".json")`
   and reading it back, **paired with the node route failing** — the second is what makes the first
   necessary, and without it the test would pass against an implementation where `raw` was
   redundant. The example must not teach a mutation, for § 2's reason.
4. **The filings.** The chartering entry struck, recording that its own framing measured the wrong
   direction; § 2's shallow-copy hole filed **with the pin consequence named**, since a closer who
   deep-copies without reading `test_per_condition_cfgs_are_not_the_same_object` will defuse it; and
   § 2's node-to-writer instance appended to the existing write-side entry rather than given a
   heading of its own.

---

## 4. What is NOT in this slice

- **Removing `raw`.** Argued out in § 1 on four grounds, one of them new since W2 filed it: the
  package is published.
- **Coding the bare `TypeError`.** § 2: an existing entry's class, and a write-side change rather
  than a documentation one.
- **Deep-copying `raw`.** § 2: it would defuse a shipped pin, and a slice may not weaken one to
  close a defect. Filed with what its closer owes.
- **Giving nested nodes a `raw`.** It would cost a parameter name at every depth rather than one at
  the root, which is the trade § The importable surface already rules on — and `cfg.raw` reaches
  every nested mapping anyway, since what it returns is a plain `dict` whose values are the
  document's own — which is § 2's finding seen from the other side.
- **A second accessor** (`as_dict`, `to_mapping`). One name is already spent; a second spends
  another to say the same thing, and § The importable surface is an enumerated list for a reason.
