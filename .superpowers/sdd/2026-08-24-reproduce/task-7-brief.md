## Task 7

**The config write-back.** Design Decision 11.

Write `configs/<name>/config.yaml` in the checkout by **re-serializing the record's embedded config**,
with `data.input_dir` and `data.output_dir` blanked and each marked
`# REQUIRED: set to your local copy`.

**Not from the byte copy, for three measured reasons** — it does not exist in the bundle form
(correction 24); locating two keys inside arbitrary YAML text to blank them is a text scan over a
structure, which is the proxy this repo keeps paying for; and where the record's config and a byte copy
disagree, the record is what produced the numbers. § Reproducing on another device says the paths are
*"blanked and **marked**"*, and core writing a comment means core is generating the YAML.

**The write is self-checked, and this is the task's central assertion.** `hashes.covered_config` excludes
`metadata`, `data.input_dir` and `data.output_dir` (correction 9), so:

```python
written = yaml.safe_load(target.read_text())
if hashes.parameters_hash(written) != record["parameters_hash"]:
    ...  # E-REPRODUCE-CONFIG-WRITEBACK, exit 1
```

**Blind to the blanking, sensitive to a lossy round trip** — a re-serialization that drops or retypes a
key moves the hash. That is the two branches that can differ, and it was checked in advance.

**Two reported facts, neither a refusal.** `parameters_hash` over the clone's own committed
`configs/<name>/config.yaml` (a pure function of the file — § CLI reference says so of `diff`), reported
*identical* or *DIFFERS* beside the recorded `provenance.git.config_committed`; a `DIFFERS` under
`config_committed: true` is a real fact about the record. And the comment loss (correction 25) is
disclosed, naming where the comments still live: the run directory's own `config.yaml` in the
run-directory form, and **nowhere** in the bundle form.

**Fixture M**, two arms. **The second arm is what makes the comparison non-vacuous**: with
`config_committed: true` and no edit, `identical` is the answer whether the code compares anything or not.

**Mutations:** write the config from the byte copy (Fixture F — the bundle form has none, so the mutation
cannot produce a config there at all); skip the `parameters_hash` check (a Fixture M arm whose record's
`config` has one key retyped by the fixture, so the round trip is lossy on purpose).

**Must not touch:** `hashes.py`, `run_record.py`, `validate.py`.

---

