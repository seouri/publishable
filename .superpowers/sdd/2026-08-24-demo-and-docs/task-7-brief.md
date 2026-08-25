## Task 7

**Binding corrections: 27, 30.**

**`docs`' dispatch.** Wire `publishable docs`, taking **no arguments**, walking up from `Path.cwd()`.

> **RULING FF (binding, restated here):** `docs` and `list-templates` **take no path**, and that is the
> **documented exception already stated at `E-GIT-NO-REPO`'s § Errors row** — *"the creation commands
> walk up from `Path.cwd()` … the one place `CLAUDE.md` § Invariants' … does not apply."* **Reuse it;
> do not mint a second one.** Cost if wrong: a second explanation of one rule, which is how a rule
> acquires two sources of truth.

`docs` catches `E-GIT-NO-REPO` **by code** and re-reports it through its own credential-bearing
`Collector` at exit `1` — never raises it into `main`, which applies **no redaction** (correction 30).

**Behaviour:** rewrite every region of the four that the README holds; **name on stdout every one it did
not find**, at exit `0`. A README holding **none** of the four is `E-DOCS-NO-REGIONS` at exit `1`; no
README at the root is `E-DOCS-NO-README` at exit `1`.

**Mutations:** design § 10 row 4, plus turning the "names what it did not find" line into a `pass` and
confirming a test fails on the **stdout content**, not on the exit code.

**Must not touch:** `NOT_BUILT_COMMANDS` — that is task 13's, and removing a key early breaks
guard-pin arm F, whose editor you are not.

---

