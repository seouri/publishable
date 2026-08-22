# H5a batch 4 (task 10) — review

Reviewed at `b55e3a3`, branch `h5a-artifacts-write-side`. Commits under review: `91a338f` (task 10),
`b55e3a3` (report). Touched `src/publishable/coercion.py`, `docs/reference.md`,
`tests/test_coercion.py`, `tests/test_apparatus.py` (plus `progress.md` and the report) — **no test
file that holds a guard-pin arm**, confirmed by `git show --stat 91a338f`.

## Verdicts

- **Spec compliance: PASS, with one Major to close before this branch merges.** Decision 7 is built
  exactly as specified: one branch, after the exact-type test and before the `__len__` guard,
  `str.__str__` rather than `str()`, `str` only rather than all four `_SCALARS` types, and the
  `np.bytes_` refusal argued from `_SCALARS` rather than asserted. Both § Errors rows the widening
  reaches do derive their scope and correctly needed no edit. What fails is controller requirement 4
  in the one direction nobody checks: the retirement sentence shipped in `docs/reference.md` names a
  retirement that **no code in this repo produces**, and it is the very case the plan's correction 6
  measured as *already working*.
- **Task quality: PASS.** The blast radius was enumerated by reading and confirmed by grep, and my
  independent enumeration found the same seven call sites and no eighth. All three prescribed
  mutations reproduce exactly as reported, including the claim that (iii) is discriminating **only**
  on the enum arm. The `noqa: UP042` decision is correct and load-bearing. Two things the report did
  not claim and I checked anyway hold. The deductions are one over-broad claim about
  `_coerce_estimate` and one un-updated justification.

## Gates — all run in the foreground

| Gate | Result |
|---|---|
| `uv run ruff check .` | `All checks passed!` |
| `uv run ruff format --check .` | `93 files already formatted` |
| `uv run mypy` | `Success: no issues found in 52 source files` |
| `uv run pytest` | **2854 passed, 1 skipped, 2 xfailed** (185s) — the expected count |

`__pycache__` cleared before the run; no `pytest-of-*` dirs existed. **Tree left clean** —
`git status --porcelain` empty after every mutation and probe, each reverted by copying a saved
pre-mutation file back and re-verified by re-running (never by `git status` alone), the coercion
file additionally `diff`ed byte-identical against its backup.

---

## Findings

### Major 1 — `docs/reference.md:1238`: the shipped retirement sentence claims a resolver retirement that no code produces, and contradicts the plan's own measurement

**The collision, first, because it is what makes this unreconcilable.** Plan correction 6 — the
correction that put this task ahead of tasks 6 and 9 — reads: *"a resolver yielding an `np.str_`
attribute, **which works today**, refuses."* The sentence this task shipped says that same value
*"used to be refused as structural."* The document and the plan's measurement contradict each other
in the one case the ordering exists to protect. The obvious defence — *the four documents are
normative and present tense for an unbuilt surface is correct* (§ Misreadings) — covers *"now
coerces"* (true once task 6 lands) and **cannot** cover *"used to be refused"*: that path went
pass-through → coerced and never through a refusal, so the clause is false under every reading,
before and after.

The new sentence reads: *"**This retires a refusal:** a resolver-yielded `np.str_` attribute value,
and an `np.str_` apparatus fact, both used to be refused as structural … and now coerce instead."*
The apparatus half is true. **The resolver half is false in both directions**, verified by running:

- **It was never refused.** `src/publishable/units.py` calls `coerce_scalars` nowhere (`grep -rn
  'coerce_scalars' src/` → runner, apparatus, cli ×3, artifacts ×2; no units.py hit), and
  `_from_resolver` at `units.py:438` projects `attributes={a: unit.attributes[a] …}` with no
  coercion. Run: `_decode_parquet(_encode_parquet([{"unit": "u1", "site": np.str_("north"), "v":
  1.0}]))` → `[{'unit': 'u1', 'site': 'north', 'v': 1.0}]`. A resolver-yielded `np.str_` attribute
  writes cleanly today and wrote cleanly before this task — which is **exactly** what plan
  correction 6 measured (*"a resolver yielding an `np.str_` attribute, **which works today**"*) and
  is the whole ground for ordering task 10 ahead of tasks 6 and 9.
- **It does not now coerce.** Nothing coerces a roster attribute value until **task 6** lands; that
  is task 6's entire payload (design Decision 6).

So a normative document asserts a retirement on a surface with no coercion at either end. After task
6 lands the "now coerces" half becomes true and the *"used to be refused"* half stays permanently
false, because that path went straight from *pass-through* to *coerced* and never through a refusal.

**Why Major and not Minor.** This is the § Misreadings row inverted — a documented rule with no code
behind it — shipped in the paragraph whose job is to state what changed, and the false clause is
about the one case this task's ordering exists to protect. A reader debugging a resolver is sent to a
history that did not happen.

**Remedy (task 10's own paragraph, not a later task's).** Name the retirements that exist: an
`np.str_`/`str`-subclass value at `io.record`, at a step's return, at a template's `aggregate` and at
a derived metric (all four verified by mutation (i) below), and the `np.str_` apparatus fact. Leave
the resolver surface to task 6, which owns both the coercion and Fixture R. *Prefer deleting a claim
to rewriting it.*

### Minor 1 — `src/publishable/coercion.py:168`: `Estimate.n` is a THIRD retirement, and the report's claim about `_coerce_estimate` is wider than the code

`_coerce_estimate` calls `_coerce_one` on `n` as well as on `value` and each `ci95` bound. Verified
by running, on the pre-task code (mutation (i) applied): `Estimate(value=0.5, n=np.str_("612
pairs"))` raised `ContractError` · `E-STEP-RETURN-TYPE`; unmutated it returns `'612 pairs'`. That is
a refusal that **stops firing outright** — not a code move — while the report states of
`_coerce_estimate` that it is *"refused both before and after, only the code moves"*, and controller
requirement 4 asks for every retiring refusal to be stated as one. No document row goes wrong (§ The
`Estimate` prose already permits a label `n`, and the new mechanism clause covers the coercion), and
the consequence is nil — Minor, not Major. **Repaired at the same site as Major 1**: the rewritten
retirement sentence is where it is named, and what is owed for `n` beyond that is an **arm**, not
prose.

### Minor 2 — `src/publishable/coercion.py` module docstring: the justification was not re-read when the guard changed

The module docstring still says *"which is why `__len__` is the refusal test: a NumPy array satisfies
every one of those protocols too, but it also has `__len__`"*. As a general statement that is now
false — `np.str_` has `__len__` and coerces (verified by running). The `reference.md` paragraph this
docstring paraphrases was updated in the same commit; the paraphrase was not. `_coerce_one`'s own
inline comments are correct and complete, so this is documentation drift inside one file rather than
a wrong guard. (`CLAUDE.md` § Habits: *when you change a guard, re-read its justification.*)

### Minor 3 — the ordering constraint of correction 6 is enforced at the shared function only, and the resolver surface is pinned by nothing

Verified by running: removing the branch, and moving it below the `__len__` guard, each fail the
same 5 tests, so a later slice deleting or displacing it is caught. What is **not** pinned is the
property the window would have broken — a resolver-yielded `np.str_` attribute resolving. `grep -rn
'np.str_' tests/` returns hits in `tests/test_coercion.py` and the one new arm in
`tests/test_apparatus.py` and nowhere else. The plan foresaw this (*"No test covers either, so the
window is invisible to the suite — which is the reason to order it rather than to trust green"*) and
chose ordering over a pin, so this is not a deviation; it is a hole to close in **task 6's Fixture
R**, and Major 1 makes it load-bearing, since `reference.md` now asserts that behaviour.

---

## What I attacked, and what each was verified by

**1. The blast radius, enumerated independently.** Read `src/` first, then `grep -rn 'coerce_scalars'
src/`: **seven** call sites in five modules — `runner.py:785` (a step's return), `apparatus.py:193`
(`check_facts`), `cli.py:812` (`aggregate`), `cli.py:2922` (a derived metric), `cli.py:2974` (a
null-test draw), `artifacts.py:668` and `:691` (`io.record`, both branches) — plus `coercion.py`'s
internal `_coerce_estimate` on `value`, each `ci95` bound and (unnamed by the report) `n`. **No
eighth site.** Same list as the report's. What changed per caller: the first six all move from
`E-STEP-RETURN-TYPE` to an exact-`str` value, which is the point; `apparatus.py:193` retires
`E-APPARATUS-FACT-TYPE` for that shape; `_coerce_estimate` moves two codes and retires one refusal
(Minor 1).

**§ Errors rows, checked one by one against the widened code:**

| Row | Scope after the widening |
|---|---|
| `E-STEP-RETURN-TYPE` (`reference.md:1116`) | derives — *"a scalar core can coerce to one"*. Still true |
| `E-APPARATUS-FACT-TYPE` (`:1131`) | derives — *"`bool`, `int`, `float`, `str`, `None`, **or what core coerces to one**"*. An `np.str_` is now the third clause rather than outside the set. No edit needed, exactly as the brief predicted |
| `E-STEP-ESTIMATE-VALUE` / `-CI95` (`:1115`) | derives — *"whose `ci95` is not two numbers …, or whose `value` is not a number"*. A coerced `str` is not a number, so the row already covers the shape whose code moved **into** it (attack 3: it derives, it does not enumerate — verified by reading the row, and by running that the two codes raised are the two the row names) |
| § The `Estimate` prose (`:2483–2485`) | derives the same way |

**A blast-radius item the report did not enumerate, which holds.** `check_facts` runs its credential
containment check **before** the scalar walk (`apparatus.py:166–189`) and guards it with
`isinstance(value, str)` — which an `np.str_` and a `str`-Enum member both satisfy. Verified by
running: a fact `np.str_("url?key=tok9")` against credential `tok9` raises
`E-APPARATUS-FACT-CREDENTIAL`, and so does a `str`-Enum fact whose value is a credential. **The
retirement opens no credential leak**, and it would have if the walk had come first.

**A third thing this review owes, and it is NOT a finding against task 10: one field of the one
exception type is exempt from the one shared rule.** `_coerce_estimate` returns
`Estimate(value=coerced_value, ci95=coerced_ci95, n=_coerce_one(...), method=value.method)` —
`method` never passes through `_coerce_one`, and its only guard is the truthiness test at
`coercion.py:120`. Verified by running: `coerce_scalars({"d": Estimate(value=0.5, ci95=[0.1, 0.9],
method=np.str_("bootstrap"))}, "s", scope="summary")["d"].method` is still `np.str_`, and
`yaml.safe_dump` on it raises **`RepresenterError`** — the traceback-instead-of-diagnostic this
module exists to prevent. Read: `cli.py:1144`, `:1294` and `:1383` write `interval.method` straight
into `run.yaml`, so the route to that traceback is a reported `Estimate` whose `method` came from a
library, and it costs the record after every execution is paid for. **Nothing moved here** — task 10
neither created nor widened it, and `str` was always accepted for `method` — but a blast-radius
review of *the one scalar rule every caller shares* should say which field is outside it, and this
task's own `_SCALARS` argument sharpens the asymmetry. Grepped `spec-defects.md` before calling it
new: the closest line is `:1914`, whose RESOLVED note claims the exemption *"had to coerce the
`Estimate`'s own fields"* — true of `value`, `ci95` and `n`, and not of `method`. **Unfiled. Route:
task 12**, which owns *"file what H5a leaves open"* — or an explicit decline with a reason.

**A second contained one.** The widening at `cli.py:2922/2974` lands a non-numeric derived metric on the
pre-existing `float(value)` path in `cli.py`'s resample closure, which `stats.py:1730` and `:1958`
contain with `except Exception: continue` (read, with the comments naming exactly the `float("high")`
case). A plain `str` already reached it, so `np.str_` joins a path that is already contained — no
new crash class.

**2. Two retirements, verified by running.** `np.str_` at `io.record` now returns `('a', str)` where
mutation (i) shows it raising `E-STEP-RETURN-TYPE`; `check_facts(Apparatus(facts={"m":
np.str_("r1")}), ["m"], …)` returns `{'m': 'r1'}` with `type(...) is str`, where the same call under
mutation (i) raises `E-APPARATUS-FACT-TYPE`. Both are stated in `reference.md` and pinned. The
apparatus one is the retirement the design never named and correction 9 found. **No § Errors row
still claims the retired behaviour** (table above), and a sweep of the four documents for the
coercion mechanism (`grep -n '__float__\|__index__\|__bool__\|NumPy scalar'` over README,
`design-principles.md`, `experimental-designs.md`, `reference.md`, `CLAUDE.md`) shows the mechanism
stated in exactly one place — `reference.md:1238`, the edited line — with `:1715` deriving via *"the
same coercion"*. The third retirement is Minor 1; the false one is Major 1.

**4. The `np.bytes_` refusal rests on `_SCALARS`, and all three ran.** `np.bytes_(b"a")` →
`E-STEP-RETURN-TYPE`; plain `b"a"` → `E-STEP-RETURN-TYPE`, same code; `np.str_("a")` → coerces. The
reasoning is written where a reader meets it — the branch comment (`coercion.py:191–207`) states
both grounds separately and says the `__len__` guard is no longer the answer for `np.str_`, the
guard's own comment (`:214`) says `np.bytes_` is refused there on plain `bytes`' ground, and
`reference.md:1238` carries the same split. I also ran the mutation the report did not: widening the
branch to `isinstance(value, (str, bytes))` fails both `bytes` arms, so those two arms are
discriminating rather than incidental.

**5. `str.__str__` versus `str()`, and the `noqa: UP042` adjudication — the decline is correct.**
Run: `str(Color.RED)` is `'Color.RED'` and `str.__str__(Color.RED)` is `'red'` for `class Color(str,
Enum)`; the shipped code returns `'red'` and mutation (iii) turns it into `'Color.RED'`. And run:
`str(A.RED)` for `class A(StrEnum)` is **`'red'`** — so had ruff's suggestion been taken, mutation
(iii) would have been a mutation whose two branches cannot differ, and the one fixture that
discriminates `str()` from `str.__str__` would have gone blind. I also verified the suppression is
load-bearing rather than decorative: stripping the three `# noqa: UP042` comments makes
`ruff check` report **3 errors**, and restoring them returns `All checks passed!`.

**The mechanical pass on the edited line, run rather than eyeballed.** `grep -nP "[ \t]$|\t|[\x{00a0}\x{200b}\x{feff}\x{2060}]|[0-9] x [0-9]"` over `reference.md:1238` → no match; no en dash on the
line; the paragraph adds no link or anchor, and the surrounding section's headings are untouched, so
nothing else in the pass has an input. **Module choice verified rather than inferred**, as the brief
instructed: `tests/test_estimate.py` holds **0** `E-STEP-ESTIMATE-VALUE`/`-CI95` arms and no
`_coerce_estimate`/`coerce_scalars` reference at all, `tests/test_coercion.py` holds 8 — the arms
landed beside their siblings, and no new file was created (`git show --stat`).

**6. Correction 6's ordering.** See Minor 3. Order on the branch is correct (task 10 at `91a338f`,
tasks 6 and 9 unlanded).

**7. The guard pin — none fired, none was touched.** `git show --stat 91a338f` touches neither
`tests/test_cli.py` nor `tests/test_artifacts.py`, so no arm could have been edited. Run:
`pytest tests/test_artifacts.py -k h5a_arm` → **5 passed** (B1, B2, C, E1, E2) and
`pytest tests/test_cli.py -k h5a_arm` → **4 passed** (A, D and siblings). Arms D and E1 — the halves
with **no authorized editor** — are green and byte-untouched; arm E2's `.csv` half (task 9's, sole
editor) is green and untouched; A/B1/B2/C are green and untouched.

**8. The report's two concerns.** (a) The `spec-defects.md` `np.str_`/`np.bytes_` row (line 1923,
*"OPEN. Owner H5 Artifacts"*) **is** genuinely half-stale: its `np.str_` half is dead (verified by
running), its `np.bytes_` half still holds. Striking it **is** task 12's, named in the plan's task
table (*"close the `np.str_`/`np.bytes_` row"*) — verified by reading, not assumed; leaving it was
correct. (b) The seven-caller claim checks out (attack 1). Both concerns are stated in the report's
"Other"/"Concerns" sections rather than under one heading, which is presentation, not substance.

**Mutations re-run independently, all three plus one of my own** (each reverted from a saved copy and
re-verified by re-running):

| Mutation | Result | Matches report |
|---|---|---|
| (i) remove the branch | **5 failed**, 2849 passed (full suite) — 3 coercion arms, 2 `Estimate` arms, 1 apparatus arm | yes |
| (ii) move it below the `__len__` guard | the **same 5** fail | yes |
| (iii) `str(value)` for `str.__str__(value)` | **exactly 1** fails — the enum arm; the `np.str_` arm passes | yes, including the claim that the two constructors agree on `np.str_` |
| (mine) widen to `(str, bytes)` | both `bytes` arms fail | n/a — new |

---

## What I could not check

- Whether tasks 6 and 9's briefs will carry the resolver retirement Major 1 asks to be deferred to
  them; that is a dispatch question, and the plan's own appended-correction precedent (*put the
  correction where the brief is extracted from*) is the route.
- Arm B2's `pyarrow` sha256 coupling — green here, and out of this task's reach by its own stated
  edit conditions.
