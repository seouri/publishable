# src/publishable/study.py
"""`study new` and `study add`. docs/reference.md § Studies: what a paper
reports, § Building one, § What `study add` redacts.

A study is a publication artifact, sibling to the paper, never inside the
git repository the code lives in — `study new` refuses a bundle path
resolving inside one, the same walk-up `input_dir`/`output_dir` already use
(`provenance.find_repo_root`), and refuses a bundle that already exists.
`study add` copies a run's own `run.yaml` into the bundle, through
`lineage.read_record_file` — the FILE entry, since `study add`'s argument
names a file rather than a run directory, unlike `report`'s own directory
form, which needs the run directory for `environment/repo_root.txt` and
`ReportIO` — redacts four host-identifying fields with a marker that
distinguishes "redacted" from "never captured" by the two states
themselves, and updates the bundle's one citable `code` pointer.

`cli.py` imports this module's functions inside its own `study` arm,
joining `report.py`'s own precedent of importing nothing from `cli` at all
— this module is the same shape, so `cli` depends on it and it never
depends back.
"""

import copy
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from publishable.errors import ContractError
from publishable.lineage import read_record_file
from publishable.provenance import find_repo_root

REDACTED = "<redacted by study add>"

_REDACTED_DATA_FIELDS = ("input_dir", "output_dir")


def _refuse_if_in_repo(path: Path, code: str, what: str) -> None:
    """Measured at `ebf642a` (§ Corrections, correction 12):
    `provenance.find_repo_root` RAISES `E-GIT-NO-REPO` rather than
    returning `None` when no repository is found, so "outside every repo"
    is implemented as the walk-up FAILING with that one code — caught
    specifically — rather than as a `None` return, and every other
    `ContractError` it might raise propagates unexamined. The walk-up form
    of this check is rejected as a mutation for the identical reason
    `E-DATA-IN-REPO`'s own guard is: above a path outside any repo it would
    be caught by a crash rather than by the property.
    """
    try:
        repo_root = find_repo_root(path)
    except ContractError as exc:
        if exc.code == "E-GIT-NO-REPO":
            return
        raise
    raise ContractError(
        f"{path} resolves inside the git repository at {repo_root} — {what} belongs "
        "beside the manuscript it supports, never inside the code repository it "
        "cites (docs/reference.md § Why not in the repo)",
        code=code,
    )


def study_new(bundle: Path, title: str) -> None:
    """`publishable study new <bundle> --title "..."`. Writes
    `<bundle>/study.yaml` with `title`, `authors: []` and `runs: {}` — no
    `code` block, because `code.commit` is one run's and there is no run
    yet.

    Both refusals happen before anything reaches disk, in the order the
    document states them: outside any repo, then not already a bundle.
    "Existing" means a `study.yaml` FILE is already there — not that the
    directory exists, since `~/papers/x/study` beside a manuscript is a
    directory a person may well have made first, and `study new` must
    still succeed onto it.
    """
    _refuse_if_in_repo(bundle, "E-STUDY-IN-REPO", "a study")
    if (bundle / "study.yaml").exists():
        raise ContractError(
            f"{bundle} already holds a study.yaml — `study new` never overwrites an "
            "existing bundle; choose a different path, or add runs to the one "
            "already there with `study add`",
            code="E-STUDY-EXISTS",
        )
    bundle.mkdir(parents=True, exist_ok=True)
    doc = {"title": title, "authors": [], "runs": {}}
    (bundle / "study.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))


def _load_study_doc(bundle: Path) -> dict[str, Any]:
    path = bundle / "study.yaml"
    if not path.exists():
        raise ContractError(
            f"no study.yaml at {bundle} — run `study new` first", code="E-STUDY-UNREADABLE"
        )
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ContractError(f"{path} is not valid YAML: {exc}", code="E-STUDY-UNREADABLE") from exc
    if not isinstance(doc, dict):
        raise ContractError(f"{path} did not parse to a mapping", code="E-STUDY-UNREADABLE")
    runs = doc.get("runs")
    if runs is not None and not isinstance(runs, dict):
        raise ContractError(f"{path}'s `runs` is not a mapping", code="E-STUDY-UNREADABLE")
    return doc


def _redact(record: Mapping[str, Any]) -> dict[str, Any]:
    """§ What `study add` redacts. A field PRESENT in the source becomes the
    literal marker; a field absent or `null` is left EXACTLY as it was —
    the distinction is carried by the two states themselves, never by two
    marker strings, because "never captured" is already spelled
    unambiguously in this format (`apparatus: null`).

    Four rows, all reached through the record's own nesting:
    `config.data.input_dir`/`output_dir`, `provenance.git.repo_root`,
    `provenance.environment.hostname`, `provenance.input_manifest`. Every
    HASH beside these — `input_manifest_hash`, `parameters_hash`,
    `code_hash` — is untouched, on the section's own closing argument that
    redaction here disturbs no verification. Nothing under
    `provenance.apparatus` is touched at all: § The apparatus core can only
    observe already keeps a probe's facts non-identifying, so this table
    has no apparatus row to begin with.

    `provenance.environment.hostname` is never written today (measured at
    `ebf642a`: `provenance.environment` is `{manager, python_version,
    uv_lock, uv_lock_hash}`) — it is H6's. So this branch is exercised only
    over a record synthesized by hand carrying it, and needs no special
    case: absent today is the "never captured" branch above, and it
    becomes "redacted" the day H6 writes it, with no code change here.
    """
    out = copy.deepcopy(dict(record))
    config = out.get("config")
    if isinstance(config, dict):
        data = config.get("data")
        if isinstance(data, dict):
            for field in _REDACTED_DATA_FIELDS:
                if data.get(field) is not None:
                    data[field] = REDACTED
    provenance = out.get("provenance")
    if isinstance(provenance, dict):
        git = provenance.get("git")
        if isinstance(git, dict) and git.get("repo_root") is not None:
            git["repo_root"] = REDACTED
        environment = provenance.get("environment")
        if isinstance(environment, dict) and environment.get("hostname") is not None:
            environment["hostname"] = REDACTED
        if provenance.get("input_manifest") is not None:
            provenance["input_manifest"] = REDACTED
    return out


def _apply_code_block(
    doc: dict[str, Any], record: Mapping[str, Any], name: str
) -> tuple[str, str] | None:
    """`code.commit` names ONE run's commit — the one added `--as main`,
    else the first one added. Mutates `doc` in place; returns a
    `("W-STUDY-COMMIT-MISMATCH", message)` pair when the add is neither of
    those and the run's own commit differs from the one already recorded,
    or `None` — the same `(code, message)` shape `report.py`'s
    `_bundle_cross_checks` returns, for the same reason: never raised, exit
    stays `0` regardless of what it finds.

    `code.remote` is `None` when the run's own is — a bundle never invents
    one.
    """
    git = (record.get("provenance") or {}).get("git") or {}
    commit = git.get("commit")
    remote = git.get("remote")
    existing = doc.get("code")
    if existing is None or name == "main":
        doc["code"] = {"remote": remote, "commit": commit}
        return None
    existing_commit = existing.get("commit") if isinstance(existing, dict) else None
    if existing_commit is not None and commit is not None and existing_commit != commit:
        return (
            "W-STUDY-COMMIT-MISMATCH",
            f"study.yaml's code.commit is {existing_commit}, and the run added as "
            f"{name!r} records commit {commit} — this is a notice, not a refusal: a "
            "sensitivity analysis rerun at a later commit is ordinary. Re-add "
            "`--as main` if this run should become the citable pointer instead",
        )
    return None


def study_add(bundle: Path, run_yaml: Path, name: str) -> list[tuple[str, str]]:
    """`publishable study add <bundle> <run.yaml> --as <name>`. Copies the
    record to `<bundle>/<name>.run.yaml`, redacts four host-identifying
    fields, updates `study.yaml`'s `runs` and `code` blocks, and returns any
    `(code, message)` notice pair (never raised — exit stays `0`).
    """
    doc = _load_study_doc(bundle)
    record = read_record_file(run_yaml)

    redacted = _redact(record)
    notice = _apply_code_block(doc, record, name)

    target = bundle / f"{name}.run.yaml"
    target.write_text(yaml.safe_dump(redacted, sort_keys=False))
    doc.setdefault("runs", {})[name] = {
        "file": target.name,
        "run_id": record.get("run_id"),
    }
    (bundle / "study.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))

    return [notice] if notice is not None else []
