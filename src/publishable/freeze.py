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

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

import yaml

from publishable import apparatus
from publishable.cli import declared_credential_names
from publishable.config import Config
from publishable.diagnostics import EXIT_EXTERNAL, EXIT_WRONG, Collector
from publishable.errors import ContractError, PublishableError
from publishable.runner import resolve_condition_cfg
from publishable.secrets import credential_values, load_env, missing_env
from publishable.sweep import Condition, expand
from publishable.templates.registry import (
    _claims,
    installed_template_message,
    unknown_template_message,
)
from publishable.validate import declared_credential_names_for, load_document


class _Refused(NamedTuple):
    """One refusal already reported through its own fresh `Collector`. No
    probe call was made and no ledger line was written to reach this —
    Fixture F4 pins the second half of that for every arm."""

    exit_code: int


class _Ready(NamedTuple):
    """Every gate in `_precheck` passed. What the probe round needs to run."""

    doc: dict[str, Any]
    repo_root: Path
    template: Any
    probe_name: str
    declared_facts: list[str]
    conditions: list[Condition]
    cfgs: dict[int, Config]
    credentials: dict[str, str]


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
    """
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
    )


def command_freeze(run_dir: Path) -> int:
    """`freeze`, end to end. Task 6 fills in the probe round; until then
    this only runs the refusal gate `_precheck` builds."""
    result = _precheck(run_dir)
    if isinstance(result, _Refused):
        return result.exit_code
    raise NotImplementedError("task 6 builds the probe round")
