## Task 12

**The config-operand form.** Design Decision 13.

Given a config, steps 1–3 have no input and step 5 is moot. What runs: task 5's ranking against **the
repo the config sits in** — found by walk-up from the **config path**, never from the working directory,
which is `CLAUDE.md`'s invariant — then `uv sync --locked`, then task 8's `.env` and `required_env`, then
the same closing instructions.

**It names what it did not verify** — `code_hash`, the input manifest, **and** the apparatus — rather
than reporting a match it never made. That is § Reproducing's own sentence and `diff`'s own rule for a
config side, and the three are three separate printed lines.

No `apparatus.expected.json` is written (a config records no facts) and no destination is derived, so
tasks 3's and 9's refusals are unreachable from this form. **Say so in the docstring rather than leaving a
reader to wonder** — and say it as *unreachable from this form*, not as *cannot happen*, because a comment
claiming a guarantee the code does not provide is this repo's most-repeated habit.

**Fixture N.** Asserts no directory created, `uv sync` reached, and the **three** not-verified lines as
**positive assertions** — *a control asserting only absences passes identically if nothing ran*.

**Mutation:** print two of the three not-verified lines (Fixture N — each is asserted separately, so
dropping any one fails).

**Must not touch:** anything task 3 built (the clone is not reached from this form).

---

