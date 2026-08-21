"""`freeze`: re-probe a run's apparatus mid-run, against its own ledger.

docs/reference.md § Operation commands, § The apparatus core can only
observe. `freeze` takes a run directory — never a config, never a
condition selector (`design-principles.md` § Everything is in the file) —
and re-probes the apparatus each resolved condition's `cfg` measures
through, comparing what comes back against the first-answered baseline
the run itself established. It never decides anything: the next
execution's own gate (`apparatus.check_changed`, wired into
`runner.execute_plan`) is what stops a run. See
`docs/superpowers/specs/2026-08-20-diff-freeze-design.md` Decisions 7-12
and `docs/superpowers/plans/2026-08-20-diff-freeze.md` tasks 4-6.

**Import direction, measured.** This module imports `cli.declared_credential_names`
at module scope. `cli.py`'s own module-level imports do not import `freeze`
— `cli._dispatch` imports `command_freeze` inside its own function body
(task 6), never at module scope — so this direction closes no cycle. The
reverse (this module built without that import, `cli.py` importing it at
module scope) would have.
"""

import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

import yaml

from publishable import apparatus
from publishable.cli import declared_credential_names
from publishable.config import Config
from publishable.diagnostics import EXIT_EXTERNAL, EXIT_OK, EXIT_WRONG, Collector
from publishable.errors import ContractError, PublishableError
from publishable.runner import resolve_condition_cfg
from publishable.secrets import credential_values, load_env, missing_env
from publishable.sweep import Condition, expand
from publishable.templates.registry import (
    _claims,
    installed_template_message,
    unknown_template_message,
)
from publishable.uv_support import uv_lock_info
from publishable.validate import declared_credential_names_for, load_document


class _Refused(NamedTuple):
    """One refusal already reported through its own fresh `Collector`. No
    probe call was made and no ledger line was written to reach this —
    Fixture F4 pins the second half of that for every arm."""

    exit_code: int


class _Ready(NamedTuple):
    """Every gate in `_precheck` passed. What the probe round needs to run.

    `baseline` is the SAME `Observations` gate (i) already built and
    validated the whole ledger to get — carried forward rather than
    re-read a second time (batch 4 review, Minor 9: `command_freeze` used
    to call `apparatus.replay_ledger` again, discarding this one)."""

    doc: dict[str, Any]
    repo_root: Path
    template: Any
    probe_name: str
    declared_facts: list[str]
    conditions: list[Condition]
    cfgs: dict[int, Config]
    credentials: dict[str, str]
    baseline: "apparatus.Observations"


def _refuse(c: Collector, code: str, path: str, message: str, exit_code: int) -> _Refused:
    c.error(code, path, message)
    print(c.render(), file=sys.stderr)
    return _Refused(exit_code)


def _ledger_probe_names(run_dir: Path) -> set[str]:
    """The distinct `probe` field across every `run_start`/`pre_execution`
    ledger line.

    Called only after `apparatus.replay_ledger` has already walked and
    validated every line in this file (gate (i)), so this second pass
    trusts what that one already confirmed rather than re-checking it a
    second way — it exists at all because `Observations` does not carry
    the probe name (Decision 9 fixes its shape), and gate (j) needs it.
    """
    path = run_dir / "apparatus" / "probes.jsonl"
    names: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = json.loads(raw)
        if line.get("phase") in (apparatus.PHASE_RUN_START, apparatus.PHASE_PRE_EXECUTION):
            names.add(line.get("probe"))
    return names


def _precheck(run_dir: Path) -> "_Refused | _Ready":
    """The refusal gate, in cost order (`§ Exit codes`' `dry-run` argument,
    verbatim: the cheap objection is reported before a metered call that
    was going to fail anyway):

    (a) run.yaml present                        -> E-FREEZE-RUN-ENDED       exit 1
    (b) config.yaml absent / not a mapping       -> E-FREEZE-NO-CONFIG      exit 1
    (c) environment/repo_root.txt absent/empty   -> E-FREEZE-NO-CONFIG      exit 1
    (d) load_env(repo_root)                      not a gate — answers (k)
    (e) template resolution                      -> four REUSED codes      exit 1
    (f) template declares no apparatus_probe     -> E-FREEZE-NO-APPARATUS  exit 1
    (g) sweep.yaml absent/unreadable              -> E-FREEZE-PLAN-MISSING  exit 1
    (h) re-expand + cross-check (task 5)          -> E-FREEZE-PLAN-MISMATCH exit 1
    (i) ledger has no run_start/pre_execution     -> E-FREEZE-LEDGER-MISSING exit 1
        a ledger line is malformed                -> E-FREEZE-LEDGER-UNREADABLE (inherited
                                                       from `apparatus.replay_ledger`)   exit 1
    (j) probe name vs the ledger's `probe`       -> E-FREEZE-PROBE-MISMATCH exit 1
    (k) a declared credential is unset           -> EXIT_EXTERNAL          exit 5

    **Before any of these**, a `run_dir` that is not a real directory at all is not
    `E-FREEZE-NO-CONFIG` — that code's remedy ("the run was started by a build
    before this artifact existed, or the directory was edited") answers a
    directory that exists but is missing an artifact, not a typo'd path or a
    config path passed by mistake (batch 4 review, Minor 7). `validate`'s own
    precedent for a path problem it did not anticipate is to let the `OSError`
    propagate to `main`'s generic handler, which reports it as `E-IO-FAILED` at
    exit `1` — reused here rather than answered with a narrower code of this
    module's own.
    """
    if not run_dir.is_dir():
        raise FileNotFoundError(f"{run_dir} is not a directory")

    # (a)
    if (run_dir / "run.yaml").exists():
        return _refuse(
            Collector(),
            "E-FREEZE-RUN-ENDED",
            str(run_dir),
            "run.yaml is present — that run ended, and its record is never "
            "modified. provenance.apparatus was assembled from the observations "
            "that existed when the record was written; appending an observation "
            "now would leave the ledger and the record permanently disagreeing "
            "about a run nobody can re-derive. Read the record; there is nothing "
            "to freeze.",
            EXIT_WRONG,
        )

    # (b) / (c) — one code, one remedy: both artifacts are written by the same
    # task in the same commit inside the same `RunLock` block, so a directory
    # holding one and not the other is a hand-edited directory rather than a
    # build difference.
    config_path = run_dir / "config.yaml"
    if not config_path.is_file():
        return _refuse(
            Collector(),
            "E-FREEZE-NO-CONFIG",
            str(run_dir),
            "no config.yaml in this run directory — the run was started by a "
            "build before this artifact existed, or the directory was edited; "
            "it cannot be frozen",
            EXIT_WRONG,
        )
    doc = load_document(config_path)
    if doc is None:
        return _refuse(
            Collector(),
            "E-FREEZE-NO-CONFIG",
            str(config_path),
            "config.yaml does not parse as a mapping — the run was started by "
            "a build before this artifact existed, or the directory was "
            "edited; it cannot be frozen",
            EXIT_WRONG,
        )
    repo_root_path = run_dir / "environment" / "repo_root.txt"
    if not repo_root_path.is_file():
        return _refuse(
            Collector(),
            "E-FREEZE-NO-CONFIG",
            str(run_dir),
            "no environment/repo_root.txt in this run directory — the run was "
            "started by a build before this artifact existed, or the "
            "directory was edited; it cannot be frozen",
            EXIT_WRONG,
        )
    repo_root_text = repo_root_path.read_text(encoding="utf-8").strip()
    if not repo_root_text:
        return _refuse(
            Collector(),
            "E-FREEZE-NO-CONFIG",
            str(repo_root_path),
            "environment/repo_root.txt is empty — the directory was edited; it cannot be frozen",
            EXIT_WRONG,
        )
    repo_root = Path(repo_root_text)

    # (d) — never overrides an exported variable, and safe to call twice;
    # answers (k), which is why it sits above the credential pre-check and
    # below the repo-root read.
    load_env(repo_root)

    # (e) — resolve through `_claims` rather than `get_template`, reusing the
    # four codes `validate_config`/`generate_experiment` already emit for the
    # same four states (§ Corrections against the code, correction 6).
    try:
        claims = _claims(repo_root)
    except KeyboardInterrupt:
        raise KeyboardInterrupt from None
    except BaseException as exc:
        code = exc.code if isinstance(exc, PublishableError) else "E-TEMPLATE-LOAD"
        partial = getattr(exc, "partial_templates", None) or []
        names: list[str] = []
        for cls in partial:
            names.extend(declared_credential_names_for(doc, cls))
        c = Collector()
        c.credentials = credential_values(names)
        return _refuse(c, code, "experiment_type", str(exc), EXIT_WRONG)

    name = doc.get("experiment_type", "")
    claim = claims.get(name)
    template = claim.cls() if claim is not None and claim.cls is not None else None
    if template is None:
        if claim is not None and claim.provenance == "installed":
            return _refuse(
                Collector(),
                "E-TEMPLATE-INSTALLED-UNSUPPORTED",
                "experiment_type",
                installed_template_message(name, claim),
                EXIT_WRONG,
            )
        plugin = doc.get("plugin")
        return _refuse(
            Collector(),
            "E-TEMPLATE-UNKNOWN",
            "experiment_type",
            unknown_template_message(
                name, sorted(claims), plugin if isinstance(plugin, str) and plugin else None
            ),
            EXIT_WRONG,
        )

    # (f)
    declared_probe = getattr(template, "apparatus_probe", None)
    if not isinstance(declared_probe, str) or not declared_probe:
        return _refuse(
            Collector(),
            "E-FREEZE-NO-APPARATUS",
            "experiment_type",
            f"the resolved template `{name}` declares no `apparatus_probe` — "
            "nothing to re-probe; this experiment does not measure through an "
            "apparatus",
            EXIT_WRONG,
        )
    declared_facts = list(getattr(template, "apparatus_facts", None) or [])

    # (g) — one code, one remedy: the run died before its plan was written,
    # or the directory was edited.
    sweep_path = run_dir / "sweep.yaml"
    if not sweep_path.is_file():
        return _refuse(
            Collector(),
            "E-FREEZE-PLAN-MISSING",
            str(sweep_path),
            "no sweep.yaml in this run directory — the run died before its "
            "plan was written, or the directory was edited",
            EXIT_WRONG,
        )
    try:
        recorded = yaml.safe_load(sweep_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return _refuse(
            Collector(),
            "E-FREEZE-PLAN-MISSING",
            str(sweep_path),
            f"sweep.yaml does not parse: {exc}",
            EXIT_WRONG,
        )
    if not isinstance(recorded, Mapping) or not isinstance(recorded.get("conditions"), list):
        return _refuse(
            Collector(),
            "E-FREEZE-PLAN-MISSING",
            str(sweep_path),
            "sweep.yaml does not hold a `conditions` list — the run died "
            "before its plan was written, or the directory was edited",
            EXIT_WRONG,
        )

    # (h) — re-expand the copied config and cross-check the FULL four-tuple
    # per condition (§ Corrections, correction 8): `index`, `label`,
    # `values` and `is_baseline`. `values` is the field that determines the
    # cfg a probe is called under, and under `ablate`/a declared `baseline`
    # a label can hold still while `values` moves — a two-field check would
    # pass a config copy whose conditions probe different parameters than
    # the run does. `design_digest` is deliberately NOT part of this check:
    # it covers `data.units`/`sweep.groups`, neither of which affects the
    # cfg a probe is called under, so checking it would guard a property
    # `freeze` does not depend on. A plain `parameters` edit changing every
    # cfg is a residual this check cannot see either — no `parameters_hash`
    # is recorded until `run.yaml` — named rather than half-covered.
    conditions = expand(doc)
    cfgs = {c.index: resolve_condition_cfg(doc, c) for c in conditions}
    recorded_conditions = recorded["conditions"]
    if len(recorded_conditions) != len(conditions):
        return _refuse(
            Collector(),
            "E-FREEZE-PLAN-MISMATCH",
            str(sweep_path),
            f"sweep.yaml records {len(recorded_conditions)} condition(s), but "
            f"the config copy re-expands to {len(conditions)} — the run "
            "directory or the config copy was edited; do not trust either",
            EXIT_WRONG,
        )
    for cond, rec in zip(conditions, recorded_conditions, strict=True):
        if not isinstance(rec, Mapping):
            return _refuse(
                Collector(),
                "E-FREEZE-PLAN-MISMATCH",
                str(sweep_path),
                f"condition {cond.index}'s recorded entry is not a mapping — "
                "the run directory or the config copy was edited; do not "
                "trust either",
                EXIT_WRONG,
            )
        mismatch: str | None = None
        if rec.get("index") != cond.index:
            mismatch = "index"
        elif rec.get("label") != cond.label:
            mismatch = "label"
        elif dict(rec.get("values") or {}) != dict(cond.values):
            mismatch = "values"
        elif bool(rec.get("is_baseline")) != cond.is_baseline:
            mismatch = "is_baseline"
        if mismatch is not None:
            return _refuse(
                Collector(),
                "E-FREEZE-PLAN-MISMATCH",
                str(sweep_path),
                f"condition {cond.index}'s `{mismatch}` disagrees with "
                "sweep.yaml's recorded plan — the run directory or the "
                "config copy was edited; do not trust either",
                EXIT_WRONG,
            )

    # (i)
    try:
        baseline = apparatus.replay_ledger(run_dir)
    except ContractError as exc:
        return _refuse(
            Collector(), exc.code, str(run_dir / "apparatus" / "probes.jsonl"), str(exc), EXIT_WRONG
        )
    if not baseline.facts_document():
        return _refuse(
            Collector(),
            "E-FREEZE-LEDGER-MISSING",
            str(run_dir / "apparatus" / "probes.jsonl"),
            "no run_start or pre_execution line in the ledger — the run has "
            "not probed yet, so there is no baseline, and probing now would "
            "pin a fact the run's own gate never adopted",
            EXIT_WRONG,
        )

    # (j) — `templates/**` is hashed but freely editable while a run
    # executes, and `freeze` resolves the template NOW. Probing a different
    # apparatus than the run measures through, and reporting `unchanged`, is
    # worse than not probing.
    ledger_probes = _ledger_probe_names(run_dir)
    if declared_probe not in ledger_probes:
        return _refuse(
            Collector(),
            "E-FREEZE-PROBE-MISMATCH",
            "experiment_type",
            f"the resolved template declares `apparatus_probe: {declared_probe}`, "
            f"but the ledger records {sorted(n for n in ledger_probes if n)!r} — "
            "templates/** was edited mid-run; check out the tree the run "
            "started from",
            EXIT_WRONG,
        )

    # Credentials, now that the template and a condition set both exist —
    # the same two collectors `validate` checks, from the same expanded
    # conditions.
    credential_names = declared_credential_names(doc, template, conditions)
    credentials = credential_values(credential_names)

    # (k) — checked before the probe, at exit 5: without this pre-check, a
    # credential the run holds but this shell lacks would arrive as
    # `E-APPARATUS-RAISED` after a metered call. Same code, one wasted call.
    missing = missing_env(credential_names)
    if missing:
        c = Collector()
        c.credentials = credentials
        return _refuse(
            c,
            "E-APPARATUS-RAISED",
            "experiment_type",
            f"declared credential(s) not set in this shell: {', '.join(missing)} "
            "— `freeze` runs in a different shell from the run that is "
            "executing, and a credential the run holds may simply not be "
            "exported here; check `.env` and this shell's own environment",
            EXIT_EXTERNAL,
        )

    return _Ready(
        doc=doc,
        repo_root=repo_root,
        template=template,
        probe_name=declared_probe,
        declared_facts=declared_facts,
        conditions=conditions,
        cfgs=cfgs,
        credentials=credentials,
        baseline=baseline,
    )


def _hash_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _warn_lock_moved(ready: "_Ready", run_dir: Path) -> None:
    """`W-FREEZE-LOCK-MOVED` (Decision 10): a warning, never a code change —
    nothing mid-run re-checks the lockfile, so an exit `1` here would tell a
    scheduler to act on something that will not stop the run. Computed
    against the captured copy's own bytes, never a captured hash, since
    `uv_lock_info` only ever hashes a real file on disk and the captured
    copy is the one artifact that answers "what did the run start with".

    **Absent on the CAPTURED side is not a move.** A captured copy that
    does not exist means nothing was captured at run start — the `not
    captured` case `diff` also uses — so there is nothing to warn about
    regardless of what the repo holds now; a project with no lockfile then
    and none now must not warn on every scaffolded run. The current side
    IS guarded when the captured side exists: a repo whose `uv.lock` was
    deleted since the run started still warns, because `uv_lock_info`
    answers `(None, None)` for a missing file and that disagrees with any
    non-empty captured hash (batch 4 review, Minor 4 — the prior wording
    claimed the absent-is-quiet rule for "either side", which is false of
    this one; narrowed rather than rewritten to keep a false claim true).
    """
    captured = run_dir / "environment" / "uv.lock"
    if not captured.is_file():
        return
    captured_hash = _hash_bytes(captured.read_bytes())
    _, current_hash = uv_lock_info(ready.repo_root)
    if current_hash != captured_hash:
        warn_c = Collector()
        warn_c.warn(
            "W-FREEZE-LOCK-MOVED",
            str(captured),
            "the repo's uv.lock no longer hashes to the copy captured at run "
            "start — nothing on disk changes because of this; it is reported "
            "so a reader knows the environment moved",
        )
        print(warn_c.render(), file=sys.stderr)


def command_freeze(run_dir: Path) -> int:
    """`freeze`, end to end (§ Operation commands, § The apparatus core can
    only observe). Re-probes the apparatus once per resolved condition and
    reports what it finds; it never decides anything — the next execution's
    own gate is what stops a run.

    **Reuses `apparatus.Observer` rather than calling `check_facts`/
    `append_observation`/`Observations.record`/`check_changed` directly**
    (task 6 step 1's ruling): the probe round's order — `check_facts` before
    `append_observation`, both before the gate — is H7d Part A's, and
    restating it here is exactly the drift Decision 9 exists to prevent.
    The one addition `Observer` needed for this caller is the
    `observations=` keyword `apparatus.py` now carries: without seeding it
    from `apparatus.replay_ledger`'s baseline, every incoming fact would
    establish its OWN first-answered entry and then compare against
    itself, so `freeze` would report `unchanged` on every run, including
    one whose fact moved.
    """
    result = _precheck(run_dir)
    if isinstance(result, _Refused):
        return result.exit_code
    ready = result

    # (l) — the probe call. `_probe_for` is the same three-step dispatch
    # `command_run` uses at run start; a dispatch fault here (the plugin
    # was uninstalled after the run started, say) is neither one of the
    # seven `E-FREEZE-*` codes nor a member of `apparatus.APPARATUS_CODES`
    # — `command_run`'s own dispatch wrapper routes it the same way, to
    # `EXIT_WRONG`, and this reuses that routing rather than inventing an
    # eighth code.
    try:
        probe_fn = apparatus._probe_for(ready.probe_name)
    except KeyboardInterrupt:
        raise KeyboardInterrupt from None
    except BaseException as exc:
        code = exc.code if isinstance(exc, PublishableError) else "E-PLUGIN-LOAD"
        c = Collector()
        c.credentials = ready.credentials
        c.error(code, "experiment_type", str(exc))
        print(c.render(), file=sys.stderr)
        return EXIT_WRONG

    observer = apparatus.Observer(
        probe_name=ready.probe_name,
        probe=probe_fn,
        declared_facts=ready.declared_facts,
        conditions=ready.conditions,
        cfgs=ready.cfgs,
        run_dir=run_dir,
        credentials=ready.credentials,
        observations=ready.baseline,
    )
    try:
        observer.observe_round(phase=apparatus.PHASE_FREEZE, condition_index=None)
    except ContractError as exc:
        c = Collector()
        c.credentials = ready.credentials
        c.error(exc.code, "experiment_type", str(exc))
        print(c.render(), file=sys.stderr)
        # Decision 10's split, inherited from `command_run`'s own shipped
        # containment rather than re-decided: `E-APPARATUS-RAISED` alone
        # earns `EXIT_EXTERNAL` (the apparatus itself is unreachable — "the
        # class you retry"); every other code this round can raise —
        # `E-APPARATUS-CHANGED` (a moved fact, § Operation commands: "freeze
        # reports a moved apparatus as a failure") and the remaining four of
        # `APPARATUS_CODES` — keeps `EXIT_WRONG`.
        if exc.code == "E-APPARATUS-RAISED":
            return EXIT_EXTERNAL
        return EXIT_WRONG

    # Decision 10's exit-0 row: "the observation, per condition" — the
    # facts document is the first-answered value per (condition, fact),
    # which by construction of the exit-0 path IS this round's own
    # observation (a disagreement would have raised `E-APPARATUS-CHANGED`
    # already). Decision 8: "the output states the count" — one line, the
    # number of conditions actually probed this invocation (batch 4
    # review, Minor 1 — this was printing a bare `unchanged` verdict word
    # with no observed fact and no count, unmet and undisclosed).
    facts_by_condition = observer.observations.facts_document()
    for condition in ready.conditions:
        key = apparatus.condition_key(condition.index, condition.label)
        facts = facts_by_condition.get(key, {})
        rendered = ", ".join(f"{name}={value!r}" for name, value in facts.items())
        print(f"  {key}  {rendered}" if rendered else f"  {key}  (no declared facts)")
    print(f"{len(ready.conditions)} condition(s) probed")

    warn_c = Collector()
    warn_c.credentials = ready.credentials
    observer.warn_unanswered(warn_c)
    if warn_c.findings:
        print(warn_c.render())

    _warn_lock_moved(ready, run_dir)

    return EXIT_OK
