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
themselves, updates the bundle's one citable `code` pointer, and — before
any of that reaches disk — prints any reported metric thin enough to be
disclosive and asks proceed-or-quit, refusing outright with no TTY to ask.

`cli.py` imports this module's functions inside its own `study` arm,
joining `report.py`'s own precedent of importing nothing from `cli` at all
— this module is the same shape, so `cli` depends on it and it never
depends back.
"""

import copy
import sys
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

    `provenance.environment.hostname` was never written as of `ebf642a`
    (`provenance.environment` then was `{manager, python_version, uv_lock,
    uv_lock_hash}`) — superseded by H6b task 3, which added it. The day this
    sentence describes has arrived, with no code change here: this branch,
    already written for the field's eventual arrival, now runs over every
    real record rather than only over one synthesized by hand, and Fixture E
    is the pin.
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


def _is_thin_checkable_entry(value: Any) -> bool:
    """A metric-shaped entry, structurally, never by which key it sits
    under or which block it came from. Every entry Decision 13's table
    describes carries `basis` (`"units"` or `"repeats"`) — a condition's
    own recorded/derived metric, `vs_baseline`'s and `results.contrasts[]`'s
    delta entries (which carry `basis` beside `delta`, not `value`) alike
    — or is a `reported: true` `Estimate`. A `by`-strata sub-mapping
    (attribute → level → metric → entry) carries neither, which is what
    tells it apart from a genuine metric one level up in `aggregated`.
    """
    return isinstance(value, Mapping) and ("basis" in value or value.get("reported") is True)


def _floor_metric_entries(record: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    """Every metric-shaped entry in `record` (`_is_thin_checkable_entry`),
    never by which key it sits under. Walks every place Decision 13's
    table says a thin metric can hide: each condition's `aggregated` block
    (its own top-level metrics AND its `by` strata), each condition's
    `vs_baseline`, `results.contrasts[]`, and `results.summary` — the
    UNION, not three shapes looked up in turn, so a `by` stratum or a
    declared contrast is never silently skipped.
    """
    entries: list[tuple[str, Mapping[str, Any]]] = []
    results = record.get("results")
    if not isinstance(results, Mapping):
        return entries

    def _step_block(label: str, block: Any) -> None:
        if not isinstance(block, Mapping):
            return
        for metric, value in block.items():
            if _is_thin_checkable_entry(value):
                entries.append((f"{label}.{metric}", value))
            elif isinstance(value, Mapping):
                for attribute, levels in value.items():
                    if not isinstance(levels, Mapping):
                        continue
                    for level, level_metrics in levels.items():
                        if not isinstance(level_metrics, Mapping):
                            continue
                        for sub_metric, entry in level_metrics.items():
                            if _is_thin_checkable_entry(entry):
                                # `metric` here is already the literal key
                                # `"by"` — the strata mapping's OWN key in
                                # `aggregated[step]` — so folding it into
                                # the label a second time doubled it to
                                # `...by.by[cohort=a]...`. Named once.
                                entries.append(
                                    (
                                        f"{label}.by[{attribute}={level}].{sub_metric}",
                                        entry,
                                    )
                                )

    for condition in results.get("conditions") or []:
        if not isinstance(condition, Mapping):
            continue
        # `.get("label", default)`'s default fires only on a MISSING key,
        # and a real condition's record carries `label: null` for an
        # unswept run — so this must test for `None` explicitly rather
        # than rely on the two-argument form, or every such line reads
        # the literal word `None` instead of falling back to `index`.
        label = condition.get("label")
        if label is None:
            label = condition.get("index")
        aggregated = condition.get("aggregated")
        if isinstance(aggregated, Mapping):
            for step, block in aggregated.items():
                _step_block(f"condition {label}.aggregated.{step}", block)
        vs_baseline = condition.get("vs_baseline")
        if isinstance(vs_baseline, Mapping):
            for step, block in vs_baseline.items():
                if not isinstance(block, Mapping):
                    continue
                for metric, entry in block.items():
                    if _is_thin_checkable_entry(entry):
                        entries.append((f"condition {label}.vs_baseline.{step}.{metric}", entry))

    for contrast in results.get("contrasts") or []:
        if not isinstance(contrast, Mapping):
            continue
        cid = contrast.get("id")
        for step, block in contrast.items():
            if step in ("id", "of", "against") or not isinstance(block, Mapping):
                continue
            for metric, entry in block.items():
                if _is_thin_checkable_entry(entry):
                    entries.append((f"contrast {cid}.{step}.{metric}", entry))

    summary = results.get("summary")
    if isinstance(summary, Mapping):
        # `results.summary` is nested by STEP NAME — `run_record.py`'s
        # `_results_block` writes `summary[e.step_name] =
        # summary_values(r.returned)` — so a `reported: true` `Estimate`
        # sits at `summary[step][metric]`, never at `summary[metric]`
        # directly. `report.py`'s own `_execution_rows` reads the sibling
        # `execution.get("summary")` block with the identical step-then-
        # entry nesting; this mirrors that shape rather than reading one
        # level short of it (a Critical this batch's review found: the
        # one-level-short walker made every `reported: true` `Estimate`
        # unreachable on any record `run` actually writes).
        for step, block in summary.items():
            if not isinstance(block, Mapping):
                continue
            for metric, entry in block.items():
                if _is_thin_checkable_entry(entry):
                    entries.append((f"summary.{step}.{metric}", entry))

    return entries


def thin_metric_lines(record: Mapping[str, Any], floor: float) -> list[str]:
    """Decision 13's three branches, keyed on what each entry ITSELF
    carries, never on where it was found:

    - `basis: "units"` whose `n` is a mapping (an `aggregated`/`by` entry):
      compared against `n["completed"]`.
    - `basis: "units"` whose `n` is absent (a contrast entry instead
      carries `n_paired`, or `n_of`/`n_against`): compared against
      whichever of those the entry carries — a paired contrast's
      `n_paired`, an unpaired one's EITHER side, on
      `W-STATS-CONTRAST-THIN`'s own "either side below the floor" rule.
      The design's own table names `n.completed` because it was written
      from the `aggregated` shape alone; the code outranks it, and a
      contrast entry has no such key at all.
    - `reported: true`: compared against the entry's own declared `n` —
      listed UNCONDITIONALLY when that `n` is `null`, since core has
      nothing to compare and an interval with no denominator is the
      disclosure risk the prompt exists for.
    - `basis: "repeats"`: compared against the repeat count,
      `repeat_spread`'s own `n` (its outermost level when `repeat_spread`
      is a list). Nothing in this build writes this shape — see
      `docs/superpowers/spec-defects.md`'s filing — so this branch is
      exercised only over a record synthesized by hand.
    """
    lines: list[str] = []
    for label, entry in _floor_metric_entries(record):
        basis = entry.get("basis")
        if basis == "units":
            n = entry.get("n")
            if isinstance(n, Mapping):
                completed = n.get("completed")
                if isinstance(completed, (int, float)) and completed < floor:
                    lines.append(f"{label}: n.completed={completed} < {floor}")
            elif "n_paired" in entry:
                value = entry["n_paired"]
                if isinstance(value, (int, float)) and value < floor:
                    lines.append(f"{label}: n_paired={value} < {floor}")
            else:
                for side in ("n_of", "n_against"):
                    value = entry.get(side)
                    if isinstance(value, (int, float)) and value < floor:
                        lines.append(f"{label}: {side}={value} < {floor}")
        elif entry.get("reported") is True:
            n = entry.get("n")
            if n is None:
                lines.append(f"{label}: reported estimate declares no n")
            elif isinstance(n, (int, float)) and n < floor:
                lines.append(f"{label}: reported n={n} < {floor}")
        elif basis == "repeats":
            repeat_spread = entry.get("repeat_spread")
            count: Any = None
            if isinstance(repeat_spread, Mapping):
                count = repeat_spread.get("n")
            elif isinstance(repeat_spread, list) and repeat_spread:
                first = repeat_spread[0]
                count = first.get("n") if isinstance(first, Mapping) else None
            if isinstance(count, (int, float)) and count < floor:
                lines.append(f"{label}: repeat count={count} < {floor}")
    return lines


def _confirm(lines: list[str]) -> bool:
    """The `min_reported_n` prompt. Prints the offending metrics to STDOUT
    and asks proceed-or-quit — nothing else, on `design-principles.md`
    § Everything is in the file's rule that a pause may never alter
    anything: quitting writes nothing (the caller checks the return value
    before writing anything), proceeding writes exactly what a bundle with
    no thin metric would have written. The prompt changes no bytes either
    way.

    With no TTY attached, this does not silently proceed:
    `E-STUDY-CONFIRM-REQUIRED`, because an unattended `study add` sailing
    past a disclosure warning is the automation this prompt exists to
    prevent. The list is printed before that refusal too — "study add
    prints the list and refuses."
    """
    print("The following reported metrics fall below `limits.min_reported_n`:")
    for line in lines:
        print(f"  {line}")
    if not sys.stdin.isatty():
        raise ContractError(
            "no terminal is attached to confirm — `study add` refuses rather than "
            "silently proceeding past a disclosure warning unattended; rerun "
            "interactively and answer the prompt",
            code="E-STUDY-CONFIRM-REQUIRED",
        )
    answer = input("Proceed and add this record to the bundle anyway? [y/N] ")
    return answer.strip().lower() in ("y", "yes")


def study_add(bundle: Path, run_yaml: Path, name: str) -> list[tuple[str, str]]:
    """`publishable study add <bundle> <run.yaml> --as <name>`. Copies the
    record to `<bundle>/<name>.run.yaml`, redacts four host-identifying
    fields, updates `study.yaml`'s `runs` and `code` blocks, and returns any
    `(code, message)` notice pair (never raised — exit stays `0`).

    `E-STUDY-NAME-EXISTS` is the load-bearing refusal, checked against BOTH
    `study.yaml`'s `runs` keys and the file on disk — the two can disagree
    (a hand-edited `study.yaml`, or a copy interrupted between the two
    writes) and the FILE is the thing whose overwrite loses data — and
    checked before the source record is even read. Adding the same
    `run_id` twice under two different names is permitted: the refusal is
    about the name, and a paper legitimately reports one run in two roles.

    Between reading the record and writing anything, the `min_reported_n`
    prompt runs over the record's own thin metrics, floored by the
    record's OWN embedded config — never a config in the working
    directory, since the limit is a property of the run being bundled.
    Quitting returns `[]` having written nothing, not even a partial copy.

    Checked in-repo the same way `study_new` is (whole-branch review,
    Minor 8): the three-part argument in § Why not in the repo — a
    publication artifact belongs beside the paper it supports, never
    inside the code repo it cites — is about the BUNDLE, not about which
    command last touched it, so a bundle created outside a repo and later
    enclosed by one (a `git init` a directory above it, or a move) must
    not become writable again just because `study new` already ran.
    """
    _refuse_if_in_repo(bundle, "E-STUDY-IN-REPO", "a study")
    doc = _load_study_doc(bundle)
    target = bundle / f"{name}.run.yaml"
    if name in (doc.get("runs") or {}) or target.exists():
        raise ContractError(
            f"{name!r} is already in this bundle — study.yaml's runs, or the file "
            f"at {target}, already holds a record; `main.run.yaml` silently becoming "
            "a different run is exactly the overwrite this project forbids "
            "everywhere. Re-add under a new name, or start a new bundle",
            code="E-STUDY-NAME-EXISTS",
        )

    record = read_record_file(run_yaml)

    floor = ((record.get("config") or {}).get("limits") or {}).get("min_reported_n")
    if isinstance(floor, (int, float)):
        thin = thin_metric_lines(record, floor)
        if thin and not _confirm(thin):
            # Fix round 1, Minor 3: quitting exits `0` (nothing FAILED —
            # this is a judgment call, not a refusal) but must not be
            # silent. Without a printed line, a quit and a completed add
            # are indistinguishable from the terminal alone.
            print("Quit — nothing was added to the bundle.")
            return []  # quitting: nothing written, not even a partial copy

    redacted = _redact(record)
    notice = _apply_code_block(doc, record, name)

    target.write_text(yaml.safe_dump(redacted, sort_keys=False))
    doc.setdefault("runs", {})[name] = {
        "file": target.name,
        "run_id": record.get("run_id"),
    }
    (bundle / "study.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))

    return [notice] if notice is not None else []
