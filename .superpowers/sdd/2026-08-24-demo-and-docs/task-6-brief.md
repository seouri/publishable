## Task 6

**Binding corrections: 18, 21, 22.**

**The `templates` region body, and `generate template`'s write into it.** One sub-section per template
this build can hand back a class for, with its full `parameter_spec` as a table: parameter, type,
default (or **required** when `default` is omitted), constraints, `help`. **`parameter_spec` is the
single source of truth** — do not read a second one, and do not invent a defaults file.

**An installed template gets a named line, not a table** (correction 21), and it says its spec is not
readable in this build, citing `E-TEMPLATE-INSTALLED-UNSUPPORTED`.

**Fixture:** a local template declaring one required parameter (no `default`), one `nullable=True`
`default=None`, one with `choices` and `requires_env`, and one `list` with `item_type` — the four
shapes whose rendering differs.

---

