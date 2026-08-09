import json
import re
import subprocess
from collections import namedtuple
from pathlib import Path
from typing import Any

import pytest
import yaml

from publishable import BaseStep
from publishable.cli import _apply_execution_order, main
from publishable.diagnostics import EXIT_INVOCATION, EXIT_OK, EXIT_WRONG
from publishable.errors import ContractError
from publishable.generators.experiment import generate_experiment
from publishable.replication import LABEL_JOIN
from publishable.scope import Execution

Ran = namedtuple("Ran", ["condition_index", "repeat_label"])


def run_a_project(
    tmp_path: Path, *, replication: dict[str, Any] | None = None, **overrides: Any
) -> dict[str, Any]:
    """Scaffold, configure, commit, and `run` a project end to end.

    The one end-to-end driver `test_cli.py` has: every test in this module that
    needs a real run through `main(["run", ...])` builds on this rather than
    inventing its own scaffold-and-commit dance. `overrides` lands as top-level
    keys merged onto the generated `config.yaml` (`sweep`, for instance);
    `replication` is named explicitly since every caller in this file sets it.

    Returns the run directory, the resolved paths, and `results`: one `Ran`
    entry per line of `executions.jsonl`, in the order execution actually
    produced them — the ground truth for "did the plan run in the order
    `sweep.yaml` recorded," read from the ledger rather than re-derived from
    the plan the way the thing under test builds `execution_order`.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    root = tmp_path / "proj"
    data = tmp_path / "data"
    results_dir = tmp_path / "results"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\np2\n")
    assert main(["new", str(root)]) == EXIT_OK
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(results_dir),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "an end-to-end helper run"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    if replication is not None:
        doc["replication"] = replication
    doc.update(overrides)
    cfg.write_text(yaml.safe_dump(doc))
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "helper run"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)

    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results_dir.glob("run_*"))
    lines = (run_dir / "executions.jsonl").read_text().splitlines()
    ledger = [json.loads(line) for line in lines]
    results = [Ran(e["condition"], e["repeat"]) for e in ledger]
    return {
        "root": root,
        "cfg": cfg,
        "results_dir": results_dir,
        "run_dir": run_dir,
        "results": results,
    }


def test_an_unknown_command_is_an_invocation_error(capsys):
    assert main(["frobnicate", "x"]) == EXIT_INVOCATION


def test_a_missing_argument_is_an_invocation_error():
    assert main(["run"]) == EXIT_INVOCATION


def test_run_on_a_path_with_no_repo_is_wrong_not_invalid(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("schema_version: '1.0'\n")
    assert main(["run", str(cfg)]) == EXIT_WRONG


def test_operation_commands_take_no_flags(capsys):
    assert main(["run", "cfg.yaml", "--allow-dirty"]) == EXIT_INVOCATION


def test_an_unwritable_output_dir_is_a_diagnostic_not_a_traceback(tmp_path: Path, capsys):
    """The ruled-on fix: `run`'s OSError surfaces as `E-IO-FAILED` at exit 1, never a
    bare traceback. `output_dir` existing as a *file* makes `Path.mkdir` raise
    `FileExistsError` (an `OSError` subclass) inside `allocate_run_dir` — the
    simplest way to provoke a real filesystem refusal without touching permissions,
    which don't behave uniformly across CI filesystems.
    """
    import subprocess

    import yaml

    from publishable.generators.experiment import generate_experiment

    root = tmp_path / "proj"
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\n")
    output_as_file = tmp_path / "results-is-a-file"
    output_as_file.write_text("not a directory\n")

    assert main(["new", str(root)]) == 0
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(output_as_file),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "a diagnostic, not a traceback"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "experiment"],
        cwd=root,
        check=True,
    )

    assert main(["run", str(cfg)]) == EXIT_WRONG
    err = capsys.readouterr().err
    assert "E-IO-FAILED" in err


RANDOMIZED_ACROSS_CONDITIONS: dict[str, Any] = {
    "sweep": {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]},
    },
    "replication": {
        "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}],
        "order": "randomized",
    },
}
"""2 conditions × 2 batches × 3 seeds = 12 pairs — enough that `rng.shuffle` landing on the
identity permutation is vanishingly unlikely, and with 2 conditions the shuffle actually has
condition boundaries to cross. A single-condition, 2-seed fixture doesn't exercise either
risk: it can't interleave conditions, and a 2-element shuffle has a 50% chance of doing
nothing, which would let a broken reorder pass silently.
"""


def test_sweep_yaml_records_the_order_mode_and_seed(tmp_path: Path):
    doc = run_a_project(
        tmp_path,
        sweep=RANDOMIZED_ACROSS_CONDITIONS["sweep"],
        replication=RANDOMIZED_ACROSS_CONDITIONS["replication"],
    )
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    assert sweep["order"] == "randomized"
    assert isinstance(sweep["order_seed"], int)
    assert len(sweep["execution_order"]) == len(sweep["labels"]) * len(sweep["conditions"])
    declared = [
        (c["index"], label) for c in sweep["conditions"] for label in sweep["labels"]
    ]
    recorded = [(e["condition"], e["repeat"]) for e in sweep["execution_order"]]
    assert recorded != declared, "the shuffle must actually move something"
    batches = [r.split(LABEL_JOIN)[0] for _, r in recorded]
    assert batches == sorted(batches), "batch01 pairs must all precede batch02 pairs"


def test_as_declared_records_no_order_seed(tmp_path: Path):
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 2}]})
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    assert sweep["order"] == "as_declared"
    assert sweep.get("order_seed") is None


class _RepeatStep(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {}


def test_a_plan_pair_missing_from_execution_order_is_a_core_bug():
    """`_apply_execution_order`'s invariant: every repeat-scope execution `build_plan`
    produced must have a home among `execution_order`'s pairs. `command_run` builds
    both from the same `conditions`/`repeats`, so this should be unreachable there —
    pinned directly, the way `tests/test_runner.py` pins `E-RUN-CFG-MISSING` and
    `E-RUN-SEED-MISSING` by constructing a mismatch `execute_plan` never resolves
    itself.
    """
    plan = [
        Execution(_RepeatStep, "repeat_step", "repeat", 0, None, "seedA"),
        Execution(_RepeatStep, "repeat_step", "repeat", 0, None, "seedB"),
    ]
    with pytest.raises(ContractError) as excinfo:
        _apply_execution_order(plan, [(0, "seedA")])  # "seedB" has no home
    assert excinfo.value.code == "E-RUN-ORDER-MISMATCH"


def test_the_recorded_order_is_the_order_that_ran(tmp_path: Path):
    """The realized order is a fact about the run, not a rule to re-derive.

    Uses `RANDOMIZED_ACROSS_CONDITIONS` (2 conditions) rather than a single-condition
    fixture: with one condition there is no condition boundary for a batch to cross,
    so the plan-reordering this test exists to catch could be missing entirely and
    a single-condition run would still pass.
    """
    doc = run_a_project(
        tmp_path,
        sweep=RANDOMIZED_ACROSS_CONDITIONS["sweep"],
        replication=RANDOMIZED_ACROSS_CONDITIONS["replication"],
    )
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    recorded = [(e["condition"], e["repeat"]) for e in sweep["execution_order"]]
    ran = [(r.condition_index, r.repeat_label) for r in doc["results"] if r.repeat_label]
    assert recorded == ran


# --- Task 9: the acceptance test — a nested batch × seed design, end to end -----


def test_a_nested_batch_seed_run_end_to_end(tmp_path):
    doc = run_a_project(
        tmp_path,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        replication={
            "repeats": [{"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}],
            "order": "randomized",
        },
    )
    run_dir = doc["run_dir"]
    repeat_dirs = sorted(p.name for p in (run_dir / "conditions").glob("*/*") if p.is_dir())
    # 2 conditions × 6 composed repeat labels each = 12 directories; the same 6
    # labels recur under both condition directories, so the set is 6 wide.
    assert len(repeat_dirs) == 2 * 3 * 2
    assert len(set(repeat_dirs)) == 3 * 2
    label_pattern = re.escape(LABEL_JOIN).join([r"batch0\d", r"seed\d+"])
    assert all(re.fullmatch(label_pattern, n) for n in set(repeat_dirs))
    sweep = yaml.safe_load((run_dir / "sweep.yaml").read_text())
    declared = [(c["index"], label) for c in sweep["conditions"] for label in sweep["labels"]]
    recorded = [(e["condition"], e["repeat"]) for e in sweep["execution_order"]]
    assert recorded != declared, "the shuffle must actually move something"
    batches = [e["repeat"].split(LABEL_JOIN)[0] for e in sweep["execution_order"]]
    assert batches == sorted(batches), "batches must run in declared order"
    assert len(sweep["execution_order"]) == 12


def test_the_recorded_order_seed_reproduces_the_order(tmp_path):
    a = run_a_project(
        tmp_path / "a",
        replication={
            "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}],
            "order": "randomized",
        },
    )
    b = run_a_project(
        tmp_path / "b",
        replication={
            "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}],
            "order": "randomized",
        },
    )
    sa = yaml.safe_load((a["run_dir"] / "sweep.yaml").read_text())
    sb = yaml.safe_load((b["run_dir"] / "sweep.yaml").read_text())
    assert sa["order_seed"] == sb["order_seed"]
    assert sa["execution_order"] == sb["execution_order"]


def test_a_single_level_seed_run_has_no_composed_labels(tmp_path):
    """The regression risk of introducing a level is that it appears where it should not."""
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 2}]})
    dirs = [p.name for p in doc["run_dir"].rglob("*") if p.is_dir()]
    assert not any(f"{LABEL_JOIN}seed" in d for d in dirs)
    assert not any(d.startswith("batch") for d in dirs)
