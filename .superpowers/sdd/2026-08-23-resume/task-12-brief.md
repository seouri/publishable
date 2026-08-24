## Task 12

**Pointer: Decision 8 binds this task.**

The input manifest is **compared, not rebuilt**.

- Before the lock: `manifest_hash(fresh)` against `manifest_hash(recorded)`, the recorded one read from
  `manifest/input.json`. Mismatch → `E-RESUME-INPUT-MOVED`, exit `1`.
- The **recorded** manifest travels into phases 6–10 (task 9 wires it), so phase 8's `verify_manifest`
  asks whether the inputs moved during *this* attempt.

**Correction 2 is why this task exists:** `verify_manifest(input_dir, manifest)` compares the directory
against the manifest it is handed, so a resume that rebuilt one would compare now against now and
always come back clean.

**Do not reuse `E-INPUT-CHANGED`.** That code is phase 8's end-of-run re-verification, it answers a
different question, and it has no § Errors row — adding an emit site to it would document unassigned
work in passing.

**Must not touch:** `manifest.py`; any `*.md`.

**Mutations:** compare the fresh manifest against itself (caught by a fixture that rewrites a file
under `input_dir` between the crash and the resume — two branches checked: the self-comparison passes,
the recorded comparison refuses); use the fresh manifest in phases 6–10 (caught by asserting
`run.yaml`'s `input_manifest_hash` equals the crashed run's recorded figure).

---

