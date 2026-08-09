"""Dispatch. Operation commands take paths and nothing else.

See docs/reference.md § Exit codes and diagnostics, § Generators, § Scaffolding.
"""

import importlib
import importlib.metadata
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from publishable.base_experiment import BaseExperiment
from publishable.config import Config
from publishable.diagnostics import (
    EXIT_FAILED,
    EXIT_INVOCATION,
    EXIT_OK,
    EXIT_PARTIAL,
    EXIT_WRONG,
    Collector,
)
from publishable.errors import ContractError, PublishableError
from publishable.generators.experiment import generate_experiment
from publishable.generators.step import generate_step
from publishable.hashes import code_hash, design_digest, parameters_hash
from publishable.manifest import build_manifest, manifest_hash, verify_manifest
from publishable.provenance import find_repo_root, git_provenance
from publishable.replication import resolve_repeats
from publishable.run_identity import RunLock, allocate_run_dir, point_latest
from publishable.run_record import assemble_run_yaml, run_status
from publishable.runner import attrition, execute_plan
from publishable.scaffold import scaffold_project
from publishable.scope import build_plan
from publishable.stats import collapse_repeats, summarize_step
from publishable.units import resolve_units, units_hash
from publishable.uv_support import uv_lock_info
from publishable.validate import validate_config

OPERATION_COMMANDS = {"validate", "run"}


def _load_experiment(repo_root: Path, entrypoint: str) -> BaseExperiment:
    """Import the entrypoint class from the project's own `src/` on `sys.path`.

    The entrypoint's root package is purged from `sys.modules` first: two projects
    in one process can declare the same package name (both scaffolds default to a
    layout like `cohort_pilot`), and a cached module would silently hand back the
    other project's steps instead of raising or re-importing the right one.
    """
    module_name, _, attr = entrypoint.partition(":")
    if not module_name or not attr:
        raise ContractError(
            f"entrypoint {entrypoint!r} is not `<module>:<attribute>`",
            code="E-ENTRYPOINT-IMPORT",
        )
    root_pkg = module_name.split(".", 1)[0]
    for cached in [m for m in sys.modules if m == root_pkg or m.startswith(root_pkg + ".")]:
        del sys.modules[cached]
    sys.path.insert(0, str(repo_root / "src"))
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, attr)
    except (ImportError, AttributeError) as exc:
        raise ContractError(
            f"entrypoint {entrypoint!r} could not be imported: {exc}",
            code="E-ENTRYPOINT-IMPORT",
        ) from exc
    finally:
        sys.path.pop(0)
    experiment: BaseExperiment = cls()
    return experiment


def command_validate(config_path: Path) -> int:
    c = Collector()
    validate_config(config_path, c)
    if c.findings:
        print(config_path)
        print(c.render())
    else:
        print(f"  ✓ config valid · {config_path}")
    return c.exit_code()


def command_run(config_path: Path) -> int:
    c = Collector()
    doc = validate_config(config_path, c)  # phases 1-2: resolve, walk up, load, validate
    if c.findings:
        print(config_path)
        print(c.render())
    if doc is None or c.has_errors:
        return EXIT_WRONG

    repo_root = find_repo_root(config_path)
    git = git_provenance(config_path, config_path)  # phase 3: clean src/**+templates/**
    if git.code_dirty:
        dirty_c = Collector()
        dirty_c.error(
            "E-CODE-DIRTY", "src/** or templates/**", "uncommitted changes; commit them first"
        )
        print(dirty_c.render())
        return EXIT_WRONG
    experiment = _load_experiment(repo_root, doc["entrypoint"])  # phase 3: entrypoint imports

    digest = design_digest(doc)  # phase 5: pin hashes
    repeats = resolve_repeats(doc, digest)
    labels = [r.label for r in repeats if r.label] or [""]
    plan = build_plan(experiment, conditions=[(0, None)], repeat_labels=labels)  # phase 4

    input_dir = Path(doc["data"]["input_dir"]).expanduser()
    output_dir = Path(doc["data"]["output_dir"]).expanduser()
    ch = code_hash(repo_root)
    ph = parameters_hash(doc)
    manifest = build_manifest(input_dir, doc["data"]["input_manifest_policy"])
    units_decl: dict[str, Any] | None = (doc.get("data") or {}).get("units")
    roster = resolve_units(units_decl, input_dir) if units_decl else None  # phase 5: roster
    lock_path, lock_hash = uv_lock_info(repo_root)
    if lock_path is None:
        # A warning, not an error: it must not change the exit code. There are
        # legitimate reasons to proceed unpinned — including the bootstrapping case
        # this project is in right now, where a scaffolded project cannot resolve a
        # lockfile until `publishable` is published to an index (see
        # docs/superpowers/spec-defects.md).
        warn_c = Collector()
        warn_c.warn(
            "W-ENV-UNLOCKED",
            "environment",
            f"no uv.lock found at {repo_root}; the environment is not pinned, and "
            "`reproduce` will not be able to restore it",
        )
        print(warn_c.render())

    run_dir = allocate_run_dir(output_dir, ch, datetime.now(UTC))  # phase 6: first creation
    with RunLock(run_dir):
        (run_dir / "manifest").mkdir()
        (run_dir / "manifest" / "input.json").write_text(json.dumps(manifest, indent=2))
        (run_dir / "environment").mkdir()
        # `pyproject.toml` always exists (uv is mandatory) so it is always captured;
        # `uv.lock` is copied only when one was found.
        (run_dir / "environment" / "pyproject.toml").write_bytes(
            (repo_root / "pyproject.toml").read_bytes()
        )
        if lock_path is not None:
            (run_dir / "environment" / "uv.lock").write_bytes(lock_path.read_bytes())

        results = execute_plan(  # phase 7
            plan=plan,
            run_dir=run_dir,
            input_dir=input_dir,
            cfg=Config(doc),
            repeats=repeats,
            digest=digest,
            units=roster,
            max_failed_fraction=(doc.get("limits") or {}).get("max_failed_fraction"),
        )

        status = run_status(results)
        # S2 always resolves a single condition, so every aggregation below is
        # scoped to condition_index=0 — never pooled across conditions. No roster
        # means nothing to aggregate over, so `aggregated` stays `None` rather than
        # an empty dict — `assemble_run_yaml` omits the key entirely in that case,
        # instead of every condition reporting a misleading empty `aggregated: {}`.
        aggregated: dict[int, dict[str, dict[str, Any]]] | None = None
        if roster is not None:
            counts = attrition(results, roster, 0)
            recording_steps = {
                r.execution.step_name
                for r in results
                if r.execution.scope == "repeat" and r.rows
            }
            aggregated = {
                0: {
                    step_name: summarize_step(collapse_repeats(results, step_name, 0), counts)
                    for step_name in sorted(recording_steps)
                }
            }
        changed_inputs = verify_manifest(input_dir, manifest)  # phase 8: re-verify
        if changed_inputs:
            status = "failed"
            drift_c = Collector()
            noun = "path" if len(changed_inputs) == 1 else "paths"
            drift_c.error(
                "E-INPUT-CHANGED",
                "data.input_dir",
                f"{len(changed_inputs)} {noun} changed since the manifest was built "
                f"at run start: {', '.join(changed_inputs)}",
            )
            print(drift_c.render())

        provenance: dict[str, Any] = {
            "git": {
                "repo_root": str(git.repo_root),
                "commit": git.commit,
                "branch": git.branch,
                "remote": git.remote,
                "code_dirty": git.code_dirty,
                "config_committed": git.config_committed,
            },
            "environment": {
                "manager": "uv",
                "python_version": ".".join(str(v) for v in sys.version_info[:3]),
                "uv_lock": "environment/uv.lock" if lock_path is not None else None,
                "uv_lock_hash": lock_hash,
            },
            "apparatus": None,
            "input_manifest": "manifest/input.json",
            "input_manifest_hash": manifest_hash(manifest),
            "input_manifest_changed": changed_inputs,
            "publishable_version": importlib.metadata.version("publishable"),
            "plugin_versions": {},
            # A run over a roster whose identity is not pinned is a run whose `n`
            # means nothing later: `units` and `units_hash` are `None` together
            # exactly when there is no `data.units` declaration to pin.
            "units": (
                {"n": len(roster), "key": units_decl["key"]}
                if roster is not None and units_decl is not None
                else None
            ),
            "units_hash": units_hash(roster) if roster is not None else None,
        }
        doc_out = assemble_run_yaml(  # phase 9: assemble and write
            run_id=run_dir.name,
            status=status,
            config=doc,
            code_hash=ch,
            parameters_hash=ph,
            provenance=provenance,
            results=results,
            repeats=repeats,
            aggregated=aggregated,
        )
        (run_dir / "run.yaml").write_text(yaml.safe_dump(doc_out, sort_keys=False))
        # `with` block exit releases the lock.

    point_latest(output_dir, run_dir)
    print(f"run.yaml → {run_dir / 'run.yaml'}")
    return {"completed": EXIT_OK, "partial": EXIT_PARTIAL}.get(status, EXIT_FAILED)  # phase 10


def _dispatch(command: str, rest: list[str]) -> int:
    if command in OPERATION_COMMANDS:
        if len(rest) != 1 or rest[0].startswith("-"):
            print(f"`{command}` takes exactly one path and no flags", file=sys.stderr)
            return EXIT_INVOCATION
        path = Path(rest[0])
        return command_validate(path) if command == "validate" else command_run(path)
    if command == "new":
        if len(rest) != 1:
            return EXIT_INVOCATION
        scaffold_project(Path(rest[0]))
        return EXIT_OK
    if command in ("generate", "g", "init"):
        return _dispatch_generate(command, rest)
    print(f"unknown command `{command}`", file=sys.stderr)
    return EXIT_INVOCATION


def _dispatch_generate(command: str, rest: list[str]) -> int:
    opts: dict[str, str] = {}
    positional: list[str] = []
    i = 0
    while i < len(rest):
        if rest[i].startswith("--"):
            if i + 1 >= len(rest):
                return EXIT_INVOCATION
            opts[rest[i][2:]] = rest[i + 1]
            i += 2
        else:
            positional.append(rest[i])
            i += 1
    kind = "experiment" if command == "init" else (positional.pop(0) if positional else "")
    repo_root = find_repo_root(Path.cwd())
    if kind == "experiment":
        name = opts.get("name") or (positional[0] if positional else "")
        # Every option is checked before use: a missing one is a wrong invocation
        # (exit 2), never a KeyError traceback.
        missing = [f"--{o}" for o in ("template", "input-dir", "output-dir") if o not in opts]
        if not name or missing:
            print(
                "`generate experiment` needs a name plus "
                + ", ".join(missing or ["a name"]),
                file=sys.stderr,
            )
            return EXIT_INVOCATION
        generate_experiment(
            repo_root=repo_root,
            name=name,
            template_name=opts["template"],
            input_dir=opts["input-dir"],
            output_dir=opts["output-dir"],
        )
        return EXIT_OK
    if kind == "step":
        if len(positional) != 2:
            return EXIT_INVOCATION
        generate_step(repo_root=repo_root, experiment=positional[0], step_name=positional[1])
        return EXIT_OK
    return EXIT_INVOCATION


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: publishable <command> [args]", file=sys.stderr)
        return EXIT_INVOCATION
    command, rest = args[0], args[1:]
    try:
        return _dispatch(command, rest)
    except PublishableError as exc:
        print(f"  error   {exc.code:<20} {exc}", file=sys.stderr)
        return EXIT_WRONG
    except OSError as exc:
        # The single point where an environment failure becomes a diagnostic
        # instead of a bare traceback. Exit 1, not 5: the specification reserves
        # 5 for something outside the machine, and a local filesystem refusal
        # (permissions, a read-only mount, no space left) is not that.
        detail = exc.strerror or str(exc)
        io_c = Collector()
        io_c.error(
            "E-IO-FAILED",
            detail,
            "the filesystem refused this operation — check permissions, "
            "free space, and that the path exists",
        )
        print(io_c.render(), file=sys.stderr)
        return EXIT_WRONG
