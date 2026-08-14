# tests/test_validate.py
from pathlib import Path

import pytest
import yaml
from tests.conftest import write_experiment_module

from publishable.diagnostics import Collector
from publishable.sweep import expand
from publishable.units import Unit, UnitList
from publishable.validate import (
    _check_assign,
    _check_cluster_by,
    _check_contrasts,
    _check_fold_stratify_by,
    _check_measurements,
    _check_weight_by,
    validate_config,
)


def base_config(tmp_path: Path) -> dict:
    return {
        "schema_version": "1.0",
        "experiment_type": "generic",
        "template_version": "1.0.0",
        "plugin": None,
        "metadata": {"name": "cohort-pilot", "description": "a pilot", "authors": ["A"]},
        "entrypoint": "cohort_pilot.experiment:CohortPilotExperiment",
        "data": {
            "input_dir": str(tmp_path / "input"),
            "output_dir": str(tmp_path / "results"),
            "input_manifest_policy": "hash_all",
        },
        "parameters": {
            "analysis": {
                "method": "pearson",
                "min_samples": 30,
                "confidence": 0.95,
                "drop_missing": True,
            }
        },
        "replication": {"repeats": [{"kind": "seed", "n": 5}], "order": "as_declared"},
    }


@pytest.fixture
def write_config(git_repo: Path, tmp_path: Path):
    (tmp_path / "input").mkdir(exist_ok=True)
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\n")

    def _write(overrides: dict | None = None) -> Path:
        doc = base_config(tmp_path)
        for dotted, value in (overrides or {}).items():
            node = doc
            *heads, leaf = dotted.split(".")
            for h in heads:
                node = node[h]
            if value is _DELETE:
                del node[leaf]
            else:
                node[leaf] = value
        path = git_repo / "configs" / "cohort-pilot" / "config.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(doc))
        return path

    return _write


_NONDET_EXPERIMENT = """\
from publishable import BaseExperiment, BaseStep


class Step01Measure(BaseStep):
    scope = "repeat"
    nondeterministic = True

    def run(self, cfg, io):
        return {}


class CohortPilotExperiment(BaseExperiment):
    steps = [Step01Measure]
"""

_BROKEN_EXPERIMENT = "raise RuntimeError('module scope blew up')\n"

_EXITING_EXPERIMENT = "import sys\nsys.exit(3)\n"


@pytest.fixture
def write_config_nondet(git_repo: Path, write_config):
    """`write_config`, but the entrypoint's one step declares `nondeterministic`."""

    def _write(overrides: dict | None = None) -> Path:
        path = write_config(overrides)
        write_experiment_module(git_repo, _NONDET_EXPERIMENT)
        return path

    return _write


@pytest.fixture
def write_config_broken(git_repo: Path, write_config):
    """`write_config`, but the entrypoint's module raises at import."""

    def _write(overrides: dict | None = None) -> Path:
        path = write_config(overrides)
        write_experiment_module(git_repo, _BROKEN_EXPERIMENT)
        return path

    return _write


@pytest.fixture
def write_config_exits(git_repo: Path, write_config):
    """`write_config`, but the entrypoint's module calls `sys.exit()` at import —
    a `SystemExit`, which does not inherit from `Exception`."""

    def _write(overrides: dict | None = None) -> Path:
        path = write_config(overrides)
        write_experiment_module(git_repo, _EXITING_EXPERIMENT)
        return path

    return _write


_DELETE = object()


def codes(path: Path) -> set[str]:
    c = Collector()
    validate_config(path, c)
    return {f.code for f in c.findings}


def messages_by_code(path: Path) -> dict[str, str]:
    c = Collector()
    validate_config(path, c)
    return {f.code: f.message for f in c.findings}


def _validate_with(tmp_path: Path, overrides: dict) -> list:
    """Write a scaffolded config with `overrides` deep-merged over `base_config`,
    then return `validate_config`'s findings.

    `test_validate.py` has no existing helper of this exact shape: every other
    test in this file goes through the `write_config` fixture, which requires
    `git_repo` (a real git repo, so `data.output_dir` can be checked against it)
    and only accepts *dotted-leaf* overrides whose parent already exists in
    `base_config`. The two tests this helper serves need to replace a whole
    block (`metadata`, `data`) with a wrong-typed value, and don't need a repo —
    `_check_data`'s repo-root lookup already tolerates "no repo at all" by
    returning quietly (`E-GIT-NO-REPO`), and neither test is about that check.
    So this writes straight under `tmp_path`, with no `git_repo`, and merges
    `overrides` recursively rather than requiring dotted keys, matching the
    brief's `{"metadata": {"name": [...]}}` call shape.
    """

    def _merge(dst: dict, src: dict) -> None:
        for key, value in src.items():
            if isinstance(value, dict) and isinstance(dst.get(key), dict):
                _merge(dst[key], value)
            else:
                dst[key] = value

    doc = base_config(tmp_path)
    _merge(doc, overrides)
    (tmp_path / "input").mkdir(exist_ok=True)
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\n")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(doc))
    c = Collector()
    validate_config(path, c)
    return c.findings


def test_a_misspelled_key_anywhere_is_reported(tmp_path: Path) -> None:
    findings = _validate_with(tmp_path, {"sweeep": {"grid": {}}, "metadata": {"athors": ["x"]}})

    fields = [f.path for f in findings if f.code == "E-CONFIG-KEY-UNKNOWN"]
    assert "sweeep" in fields
    assert "metadata.athors" in fields


def test_a_non_string_top_level_key_is_a_diagnostic_not_a_traceback(tmp_path: Path) -> None:
    """A YAML mapping key need not be a string (`1: oops` parses to an `int`
    key), and `check_envelope`'s `difflib` call used to require one — a
    regression this task's own closure introduced and this test pins shut."""
    findings = _validate_with(tmp_path, {1: "oops"})

    fields = [f.path for f in findings if f.code == "E-CONFIG-KEY-UNKNOWN"]
    assert "1" in fields


def test_a_non_string_nested_key_is_a_diagnostic_not_a_traceback(tmp_path: Path) -> None:
    findings = _validate_with(tmp_path, {"metadata": {1: "oops"}})

    fields = [f.path for f in findings if f.code == "E-CONFIG-KEY-UNKNOWN"]
    assert "metadata.1" in fields


def test_a_wrong_typed_leaf_is_a_diagnostic_not_a_traceback(tmp_path: Path) -> None:
    """`validate` collects findings and never raises. Before the envelope this
    ended the process in `re.match`'s TypeError with no diagnostic at all."""
    findings = _validate_with(tmp_path, {"metadata": {"name": ["a", "b"]}})

    assert "E-CONFIG-TYPE" in [f.code for f in findings]


def test_a_wrong_typed_leaf_does_not_suppress_later_findings(tmp_path: Path) -> None:
    """A leaf fault is fatal to its field, not to the pass. A container fault
    is fatal to the pass, and that difference is the point."""
    findings = _validate_with(
        tmp_path, {"metadata": {"name": ["a", "b"]}, "data": {"input_dir": "/nonexistent"}}
    )

    codes_found = [f.code for f in findings]
    assert "E-CONFIG-TYPE" in codes_found
    assert len([c for c in codes_found if c != "E-CONFIG-TYPE"]) > 0


def test_a_wrong_typed_container_is_still_fatal(tmp_path: Path) -> None:
    """The existing early return, unchanged: later checks index into the block."""
    findings = _validate_with(tmp_path, {"metadata": ["not", "a", "mapping"]})

    assert "E-CONFIG-SHAPE" in [f.code for f in findings]


def test_a_string_budget_is_reported(tmp_path: Path) -> None:
    """Before the envelope this reported nothing: `isinstance(budget, int)`
    skipped the budget check on a string, and nothing typed the leaf either.
    A string budget can't be compared against an execution count, so this
    test pins only the type fault — the paired test below pins that the
    budget check itself still runs once the value is well-typed."""
    findings = _validate_with(tmp_path, {"limits": {"max_executions": "5"}})

    codes = [f.code for f in findings]
    assert "E-CONFIG-TYPE" in codes


def test_a_well_typed_budget_below_the_design_still_warns(tmp_path: Path) -> None:
    """The envelope must not have displaced the check it exposed. This is the
    test that fails if a fix reports the type fault and drops the warning."""
    findings = _validate_with(tmp_path, {"limits": {"max_executions": 1}})

    messages = {f.code: f.message for f in findings}
    assert "W-EXEC-BUDGET" in messages
    assert "1 conditions × 5 repeats = 5 executions exceeds 1" in messages["W-EXEC-BUDGET"]


def test_a_bool_budget_is_reported_once_and_the_check_is_skipped(tmp_path: Path) -> None:
    """`isinstance(True, int)` is `True` in Python, so a plain `isinstance(budget,
    int)` guard let a `bool` budget through into the comparison, producing a
    warning no one could act on (`"... exceeds True"`) alongside the envelope's
    own `E-CONFIG-TYPE` — reporting the same fault twice, once sensibly and once
    as nonsense. `max_executions: true` must be reported by the envelope and by
    nothing else."""
    findings = _validate_with(tmp_path, {"limits": {"max_executions": True}})

    codes = [f.code for f in findings]
    assert "E-CONFIG-TYPE" in codes
    assert "W-EXEC-BUDGET" not in codes


def test_a_string_min_reported_n_is_reported(tmp_path: Path) -> None:
    """The same silent-skip class as the budget check, one guard over in
    `_check_report_by`: `isinstance(floor, (int, float))` used to skip
    `W-STATS-REPORTBY-THIN` on a wrong-typed `min_reported_n` with nothing
    typing the leaf either. `test_a_thin_report_by_level_warns_before_the_run`
    and `test_two_thin_report_by_levels_are_diagnosed_in_a_stable_order`
    already pin that the check still runs on a well-typed floor, so this test
    covers only the type fault half of the pair."""
    findings = _validate_with(tmp_path, {"limits": {"min_reported_n": "10"}})

    codes = [f.code for f in findings]
    assert "E-CONFIG-TYPE" in codes


def test_a_wrong_typed_input_dir_does_not_crash_unit_resolution(tmp_path: Path) -> None:
    """`_check_data` guards its own `Path(input_dir)` call, but `_check_units` makes
    a SECOND, independent `Path(input_dir)` call — reached only once `data.units` is
    declared, which is exactly the shape the original three-guard survey never
    exercised (see the task report). Before `_check_units` had its own guard, this
    config crashed `validate_config` with a bare `TypeError` from `Path()`, discarding
    every finding the pass had collected up to that point — worse than no envelope at
    all, since `check_envelope` had already recorded `E-CONFIG-TYPE` for this exact
    leaf and the crash threw it away."""
    findings = _validate_with(
        tmp_path,
        {"data": {"input_dir": ["a", "list"], "units": {"from": "index.csv", "key": "p1"}}},
    )

    assert "E-CONFIG-TYPE" in [f.code for f in findings]


def test_a_wrong_typed_units_key_does_not_crash_table_resolution(tmp_path: Path) -> None:
    """`_from_table` (`units.py`) hashes `data.units.key` against a `set` of column
    names (`key_col not in columns`), which raises `TypeError: unhashable type` for a
    list or dict — not the `ContractError` `_check_units`'s `except` is built to
    catch. Before `_check_units` guarded this leaf's type before calling
    `resolve_units`, this config crashed `validate_config` the same way the input_dir
    case above did, for the same reason: a leaf fault is deliberately non-fatal, so
    `_check_units` reaches `resolve_units` on a still-malformed `doc`."""
    findings = _validate_with(
        tmp_path,
        {"data": {"units": {"from": "index.csv", "key": ["a", "list"]}}},
    )

    assert "E-CONFIG-TYPE" in [f.code for f in findings]


def test_a_wrong_typed_units_attribute_item_does_not_crash_table_resolution(
    tmp_path: Path,
) -> None:
    """`LEAF_TYPES` types `data.units.attributes` itself a `list`, and a list is what
    a config with `attributes: [["a", "list"]]` declares — `check_envelope` reports
    nothing, because the outer shape is right; only an ITEM inside it is wrong, the
    same class of gap `sweep.grid`'s per-value checks exist for, one leaf table
    cannot name a dotted path for a list element. `_from_table` (`units.py`) checks
    each name against `RESERVED_FIELDS` (a tuple — tolerates an unhashable name) and
    then against `columns` (a `set` — `TypeError: unhashable type` for a list or
    dict). Unlike the `input_dir`/`key` guards above, nothing else in this pass
    reports this fault, so `_check_units` reports it itself (`E-UNITS-ATTR-MISSING`,
    the same code a string name the table doesn't have gets) rather than silently
    skipping resolution — a silent skip here is exactly the failure mode this whole
    slice exists to close."""
    findings = _validate_with(
        tmp_path,
        {
            "data": {
                "units": {"from": "index.csv", "key": "patient_id", "attributes": [["a", "list"]]}
            }
        },
    )

    codes_found = [f.code for f in findings]
    assert "E-UNITS-ATTR-MISSING" in codes_found


def test_a_wrong_typed_units_attribute_item_does_not_crash_report_by(tmp_path: Path) -> None:
    """`_check_report_by` builds `declared = set(data.units.attributes)` directly —
    a second, independent crash site over the same list-of-items gap, found while
    verifying the `_check_units` fix above rather than named by the review: a
    non-string item made `set(...)` itself raise before `_check_report_by`'s own
    per-entry checks ever ran, discarding every finding collected so far exactly
    like the `_check_units` case did."""
    findings = _validate_with(
        tmp_path,
        {
            "data": {
                "units": {"from": "index.csv", "key": "patient_id", "attributes": [["a", "list"]]}
            },
            "statistics": {"report_by": ["cohort"]},
        },
    )

    codes_found = [f.code for f in findings]
    assert "E-UNITS-ATTR-MISSING" in codes_found
    assert "E-STATS-REPORTBY-UNKNOWN" in codes_found


def test_a_wrong_typed_units_attribute_item_does_not_crash_contrasts(tmp_path: Path) -> None:
    """`_check_contrasts` builds `declared_attrs = set(data.units.attributes)` the
    same way `_check_report_by` does — the third site over the same gap, guarded
    the same way."""
    findings = _validate_with(
        tmp_path,
        {
            "data": {
                "units": {"from": "index.csv", "key": "patient_id", "attributes": [["a", "list"]]}
            },
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman"]},
            },
            "statistics": {
                "contrasts": [
                    {
                        "id": "s",
                        "of": "method=spearman",
                        "against": "baseline",
                        "within": {"cohort": "a"},
                    }
                ]
            },
        },
    )

    codes_found = [f.code for f in findings]
    assert "E-UNITS-ATTR-MISSING" in codes_found


def test_a_valid_config_reports_nothing(write_config):
    assert codes(write_config()) == set()


def test_an_empty_description_is_required(write_config):
    assert "E-META-REQUIRED" in codes(write_config({"metadata.description": ""}))


def test_an_unknown_key_is_a_typo_by_construction(write_config):
    path = write_config()
    doc = yaml.safe_load(path.read_text())
    doc["parameters"]["analysis"]["min_sample"] = 30
    path.write_text(yaml.safe_dump(doc))
    assert "E-PARAM-UNKNOWN" in codes(path)


def test_values_are_checked_not_just_presence(write_config):
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.confidence": 1.4}))
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.method": "pearsonn"}))
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.min_samples": "30"}))


def test_a_missing_parameter_is_reported():
    """`generic`'s parameters all carry defaults, so no config it accepts can be missing
    one — deleting `analysis.method` from the fixture just falls back to its default and
    reports nothing. Exercised directly against a stub template with a required
    parameter, the same pattern as the repeat-floor test below."""
    from publishable.param import Param
    from publishable.templates.base import BaseTemplate
    from publishable.validate import _check_parameters

    class Benchmark(BaseTemplate):
        parameter_spec = {"analysis.method": Param(str)}

    c = Collector()
    _check_parameters({"parameters": {}}, Benchmark(), c)
    assert "E-PARAM-MISSING" in {f.code for f in c.findings}


def test_the_name_must_match_the_pattern_and_the_directory(write_config):
    assert "E-NAME-PATTERN" in codes(write_config({"metadata.name": "Cohort_Pilot"}))
    assert "E-NAME-DIR" in codes(write_config({"metadata.name": "cohort-pilot-v2"}))


def test_an_uninstalled_template_is_fatal(write_config):
    assert "E-TEMPLATE-UNKNOWN" in codes(write_config({"experiment_type": "llm_diagnostic"}))


def test_data_may_not_resolve_inside_the_repo(write_config, git_repo: Path):
    inside = str(git_repo / "results")
    assert "E-DATA-IN-REPO" in codes(write_config({"data.output_dir": inside}))


def test_an_unreadable_input_dir_is_reported(write_config, tmp_path: Path):
    assert "E-DATA-UNREADABLE" in codes(write_config({"data.input_dir": str(tmp_path / "absent")}))


def test_a_moved_template_version_warns_rather_than_failing(write_config):
    found = codes(write_config({"template_version": "0.9.0"}))
    assert "W-TEMPLATE-VERSION" in found


def test_a_repeat_count_below_one_executes_nothing_and_is_an_error(write_config):
    assert "E-REPL-N" in codes(write_config({"replication.repeats": [{"kind": "seed", "n": 0}]}))


def test_two_bad_repeat_levels_are_both_reported():
    """`_check_replication` collects rather than stopping, so a config with two invalid
    levels must not report only the first.

    Both levels carry `n`, the count field their kinds actually take — a `fold`
    with an `n` is now refused outright as a field its kind does not take
    (`E-REPL-LEVEL-FIELD`), so it is no longer a way to write a second invalid
    count."""
    from publishable.templates.builtin.generic import GenericTemplate
    from publishable.validate import _check_replication

    doc = {
        "replication": {
            "repeats": [
                {"kind": "batch", "n": -1},
                {"kind": "seed", "n": 0},
            ]
        }
    }
    c = Collector()
    _check_replication(doc, GenericTemplate(), c)
    found = [f for f in c.findings if f.code == "E-REPL-N"]
    assert len(found) == 2
    # an invalid design must not also produce a floor warning on top of the errors
    assert not any(f.code == "W-REPL-FLOOR" for f in c.findings)


def test_a_fold_level_now_resolves(write_config, tmp_path):
    """`fold` was refused by name through S3b; S3c's replication.py resolves it, so
    a plain `k` declares cleanly given a roster large enough to partition."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id\n" + "\n".join(f"p{i}" for i in range(1, 6)) + "\n"
    )
    found = codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "replication": {"repeats": [{"kind": "fold", "k": 5}]},
            }
        )
    )
    assert not [c for c in found if c.startswith("E-REPL")]


def test_a_fold_level_with_no_units_declared_is_refused(write_config):
    """A `fold` level partitions units; with no `data.units` there is no roster to
    partition. Left unrefused, this validated clean and then either crashed at
    `run` (`fold_members_for` zipping a fold's members against no partitions) or,
    worse, ran `k` roster-less repeats to completion while `sweep.yaml`/`run.yaml`
    described a k-fold cross-validation that never happened."""
    found = codes(write_config({"replication": {"repeats": [{"kind": "fold", "k": 5}]}}))
    assert "E-REPL-FOLD-NO-UNITS" in found


def test_fold_stratify_by_is_no_longer_refused_as_unbuilt(write_config):
    """`E-REPL-FOLD-STRATIFY-UNSUPPORTED` is retired: `partition_units` balances
    the declared stratum across the folds, so the declaration changes the split.
    What survives is the checking of the *name* — this config declares no
    `data.units` at all, so it draws the roster refusal and the unknown-attribute
    one, which is the control that must report."""
    found = codes(
        write_config(
            {"replication": {"repeats": [{"kind": "fold", "k": 5, "stratify_by": "site"}]}}
        )
    )
    assert found == {"E-REPL-FOLD-NO-UNITS", "E-REPL-FOLD-STRATIFY-UNKNOWN"}


def test_fold_k_below_two_is_refused_through_validate(write_config):
    assert "E-REPL-FOLD-K" in codes(
        write_config({"replication": {"repeats": [{"kind": "fold", "k": 1}]}})
    )


def test_fold_k_too_large_is_refused_against_the_real_roster(write_config):
    """`E-REPL-FOLD-K-TOO-LARGE` needs the resolved roster to know a ceiling
    exists at all. `_check_units` resolves it and `validate_config` threads its
    length into `_check_replication`, so this now goes end to end through
    `validate_config` rather than calling `resolve_repeats` directly. The
    fixture's `index.csv` resolves to exactly one unit (`p1`), so `k: 2` — the
    smallest valid fold count — already exceeds it."""
    found = codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "replication": {"repeats": [{"kind": "fold", "k": 2}]},
            }
        )
    )
    assert "E-REPL-FOLD-K-TOO-LARGE" in found


def test_fold_k_all_produces_a_finding_never_a_traceback(write_config):
    """This is the exact config that crashed `validate` with an uncaught
    `ValueError` before the arithmetic in `_check_replication`/`_repeat_total`
    was taught to recognize an unresolved `k: all` rather than coerce it."""
    found = codes(write_config({"replication": {"repeats": [{"kind": "fold", "k": "all"}]}}))
    assert "E-REPL-FOLD-K" in found


def test_two_levels_of_one_kind_are_refused(write_config):
    assert "E-REPL-LEVEL-DUPLICATE" in codes(
        write_config(
            {"replication": {"repeats": [{"kind": "seed", "n": 2}, {"kind": "seed", "n": 3}]}}
        )
    )


def test_a_batch_inside_another_level_is_refused(write_config):
    assert "E-REPL-LEVEL-BATCH-INNER" in codes(
        write_config(
            {"replication": {"repeats": [{"kind": "seed", "n": 2}, {"kind": "batch", "n": 3}]}}
        )
    )


def test_three_levels_are_refused(write_config):
    assert "E-REPL-LEVEL-DEPTH" in codes(
        write_config(
            {
                "replication": {
                    "repeats": [
                        {"kind": "batch", "n": 2},
                        {"kind": "seed", "n": 2},
                        {"kind": "seed", "n": 2},
                    ]
                }
            }
        )
    )


def test_two_levels_of_different_kinds_validate_clean(write_config):
    found = codes(
        write_config(
            {"replication": {"repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]}}
        )
    )
    assert not [c for c in found if c.startswith("E-REPL")]


def test_randomized_order_is_accepted(write_config):
    found = codes(
        write_config(
            {"replication": {"repeats": [{"kind": "seed", "n": 2}], "order": "randomized"}}
        )
    )
    assert "E-REPL-ORDER" not in found


def test_an_unknown_order_is_refused(write_config):
    assert "E-REPL-ORDER" in codes(
        write_config({"replication": {"repeats": [{"kind": "seed", "n": 2}], "order": "sideways"}})
    )


def test_an_unresolved_repl_code_is_not_swallowed(write_config, monkeypatch):
    """`REPL_DECLARATION_CODES` is deliberately narrow: it is today's complete list
    of refusals that are properties of the declaration, not a catch-all. A future
    code `resolve_repeats` raises that nobody has added to the set must propagate
    out of `validate_config` rather than being silently absorbed into a finding —
    this pins the `else: raise` branch, which no code exercises today."""
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _boom(doc, digest, fold_basis=None):
        raise ContractError("a future refusal nobody has classified yet", code="E-REPL-FUTURE")

    monkeypatch.setattr(validate_mod, "resolve_repeats", _boom)
    with pytest.raises(ContractError):
        validate_config(write_config(), Collector())


def test_an_unknown_repeat_kind_is_refused_through_validate(write_config):
    assert "E-REPL-KIND" in codes(
        write_config({"replication": {"repeats": [{"kind": "unknown_kind", "n": 2}]}})
    )


def test_colliding_seeds_are_refused_through_validate(write_config, monkeypatch):
    import publishable.replication as replication

    monkeypatch.setattr(replication, "_seed_for", lambda digest, index: 42)
    assert "E-REPL-SEED-COLLISION" in codes(
        write_config({"replication": {"repeats": [{"kind": "seed", "n": 3}]}})
    )


def test_an_unrecognised_sweep_key_is_refused(write_config):
    """A typo'd mode expands to zero conditions and would otherwise run nothing.
    Same argument as the unknown-parameter check: `init` writes every valid key,
    so an unrecognised one is a typo by construction."""
    found = codes(write_config({"sweep": {"gird": {"analysis.method": ["spearman"]}}}))
    assert "E-SWEEP-KEY-UNKNOWN" in found


def test_the_four_refused_modes_are_known_keys_not_unknown_ones(write_config):
    """`paired`, `ablate`, `sample`, and `groups` are each declared under their own
    identifier in `SWEEP_MODES` — none refused by `_check_unimplemented` any more,
    all four having lost that refusal across earlier tasks and this one — so
    `_check_sweep` must not report any of them as an unrecognised key."""
    for mode in ("paired", "ablate", "sample", "groups"):
        found = codes(write_config({"sweep": {mode: {"analysis.method": ["pearson"]}}}))
        assert "E-SWEEP-KEY-UNKNOWN" not in found


def test_an_axis_declaring_no_values_is_refused(write_config):
    """Zero conditions is a run that executes nothing while reporting success —
    the same reasoning as E-UNITS-EMPTY: zero is not a small study."""
    assert "E-SWEEP-AXIS-EMPTY" in codes(write_config({"sweep": {"grid": {"analysis.method": []}}}))


def test_an_empty_grid_block_is_refused_by_the_backstop(write_config):
    """`sweep: {grid: {}}` never enters the per-axis loop in `_check_sweep` — that
    loop iterates `grid.items()`, which is empty — so nothing there can catch it.
    The backstop refuses on `expand(doc)` returning zero conditions, whatever
    shape of `sweep` produced that."""
    found = codes(write_config({"sweep": {"grid": {}}}))
    assert "E-SWEEP-EXPANDS-EMPTY" in found


def test_an_empty_axis_still_gets_the_specific_diagnosis_not_just_the_backstop(write_config):
    """The backstop sits beneath E-SWEEP-AXIS-EMPTY, not in place of it: a config
    with an empty axis must still receive the specific diagnosis."""
    found = codes(write_config({"sweep": {"grid": {"analysis.method": []}}}))
    assert "E-SWEEP-AXIS-EMPTY" in found
    assert "E-SWEEP-EXPANDS-EMPTY" in found


def test_no_sweep_at_all_still_validates_clean(write_config):
    """The critical negative: no `sweep` block is the ordinary case, and a result
    check written carelessly (e.g. `if not conditions`, without the `sweep and`
    guard) would refuse it. `expand({})` returns exactly one condition."""
    found = codes(write_config({}))
    assert "E-SWEEP-EXPANDS-EMPTY" not in found


def test_a_normal_baseline_plus_grid_config_still_validates_clean(write_config):
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                }
            }
        )
    )
    assert not [c for c in found if c.startswith("E-SWEEP")]


def test_a_swept_path_must_be_a_real_parameter(write_config):
    assert "E-SWEEP-PATH-UNKNOWN" in codes(
        write_config({"sweep": {"grid": {"analysis.methd": ["spearman"]}}})
    )


def test_a_swept_path_that_resolves_is_not_flagged(write_config):
    found = codes(write_config({"sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}}}))
    assert "E-SWEEP-PATH-UNKNOWN" not in found


def test_a_swept_value_must_be_checkable_against_the_spec(write_config):
    assert "E-PARAM-VALUE" in codes(
        write_config({"sweep": {"grid": {"analysis.method": ["spearmann"]}}})
    )


def test_a_swept_value_must_render_as_a_nameable_label(write_config):
    """A label is a selector; a value needing escaping is not a name anyone can type."""
    assert "E-SWEEP-VALUE-UNNAMEABLE" in codes(
        write_config({"sweep": {"grid": {"analysis.method": ["a long sentence"]}}})
    )


def test_a_value_with_a_single_underscore_is_accepted(write_config):
    """`_` alone stays legal — only `__`, the axis separator, is refused. The value
    here is not one of the template's choices, so `E-PARAM-VALUE` still fires; what
    matters is that the label check itself does not also flag it."""
    found = codes(write_config({"sweep": {"grid": {"analysis.method": ["pearson_x"]}}}))
    assert "E-SWEEP-VALUE-UNNAMEABLE" not in found


def test_a_paired_path_must_be_a_real_parameter(write_config):
    """The identical `E-SWEEP-PATH-UNKNOWN` a `grid` axis gets, one mode over.
    Task 2 made `paired` executable without bringing the value-level checks with
    it, so a one-character typo validated clean: `resolve_condition_cfg`'s
    `setdefault` walk then *creates* `parameters.analysis.methdo`, leaving
    `analysis.method` at the config's own value in every condition while each
    still earns a distinct `parameters_hash` — one experiment executed twice and
    recorded as a two-arm sweep."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "paired": [{"analysis.methdo": "pearson"}, {"analysis.methdo": "spearman"}]
                }
            }
        ),
        c,
    )
    finding = next(f for f in c.findings if f.code == "E-SWEEP-PATH-UNKNOWN")
    assert finding.path == "sweep.paired[0].analysis.methdo"


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("pearsonn", id="outside_choices"),
        pytest.param("thirty", id="wrong_type"),
    ],
)
def test_a_paired_value_must_satisfy_its_param(write_config, value):
    """§ Validation's "Choices" and "Types" rows are properties of the value, not
    of the mode that wrote it. `pearsonn` is outside `analysis.method`'s choices;
    `thirty` is a string at the integer `analysis.min_samples`."""
    path = "analysis.method" if value == "pearsonn" else "analysis.min_samples"
    found = codes(write_config({"sweep": {"paired": [{path: value}]}}))
    assert "E-PARAM-VALUE" in found


def test_a_paired_value_containing_a_path_separator_is_refused(write_config):
    """The security-shaped case, and `CLAUDE.md`'s own named trap ("a path or a
    slashed identifier as a swept value"). A `paired` value — unlike a `baseline`
    one — IS what `label_for` renders, and the label becomes a directory segment:
    unchecked, `analysis.method: ../../evil` produces `00_method=../../evil` and
    resolves outside the condition directory. `a/b` is the minimal form."""
    found = codes(write_config({"sweep": {"paired": [{"analysis.method": "a/b"}]}}))
    assert "E-SWEEP-VALUE-UNNAMEABLE" in found


def test_a_paired_list_level_is_refused_as_unnameable(write_config):
    """A list where a scalar belongs. It renders into a label that is not a name,
    and `contrasts._free_axis_paths` compares condition values with `!=` rather
    than through a set, which is what keeps it total on an unhashable value —
    it takes `expand`'s output and cannot assume `validate` ran at all."""
    found = codes(write_config({"sweep": {"paired": [{"analysis.method": ["a", "b"]}]}}))
    assert "E-SWEEP-VALUE-UNNAMEABLE" in found


def test_a_legal_paired_axis_is_not_flagged_by_any_of_the_four(write_config):
    """The mirror: the value-level checks must not fire on the shape § Expansion
    modes tells a reader to write. Without this, deleting a check's *condition*
    rather than the check passes every test above."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "paired": [
                        {"analysis.method": "pearson", "analysis.min_samples": 30},
                        {"analysis.method": "spearman", "analysis.min_samples": 50},
                    ]
                }
            }
        )
    )
    assert not [
        code
        for code in found
        if code in {"E-SWEEP-PATH-UNKNOWN", "E-SWEEP-VALUE-UNNAMEABLE", "E-PARAM-VALUE"}
    ]


def test_the_execution_budget_is_checked_against_the_real_expansion(write_config):
    found = codes(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
                "replication": {"repeats": [{"kind": "seed", "n": 5}]},
                "limits": {"max_executions": 10},  # 3 × 5 = 15 > 10
            }
        )
    )
    assert "W-EXEC-BUDGET" in found


def test_the_budget_does_not_warn_when_the_expansion_fits(write_config):
    found = codes(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}},
                "replication": {"repeats": [{"kind": "seed", "n": 2}]},
                "limits": {"max_executions": 500},
            }
        )
    )
    assert "W-EXEC-BUDGET" not in found


def test_the_budget_passes_at_exactly_the_limit_and_fails_one_over(write_config):
    found_at = codes(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}},
                "replication": {"repeats": [{"kind": "seed", "n": 5}]},
                "limits": {"max_executions": 10},  # 2 × 5 = 10, exactly at budget
            }
        )
    )
    assert "W-EXEC-BUDGET" not in found_at

    found_over = codes(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
                "replication": {"repeats": [{"kind": "seed", "n": 5}]},
                "limits": {"max_executions": 14},  # 3 × 5 = 15 > 14
            }
        )
    )
    assert "W-EXEC-BUDGET" in found_over


def test_an_unreadable_count_that_is_not_a_word_still_leaves_the_budget_computable(write_config):
    """The skip is for a count declared as a *word* and unresolvable, not for
    every count this module can't read as a number. `n: yes` is a bool under
    `yaml.safe_load`; `resolve_repeats` runs it as one repeat, so treating it as
    unknown would suppress `W-EXEC-BUDGET` for the whole config over a typo —
    the silent-skip class this pass exists to end, reintroduced one layer up."""
    found = codes(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
                "replication": {"repeats": [{"kind": "seed", "n": True}]},
                "limits": {"max_executions": 2},  # 3 conditions × 1 repeat = 3 > 2
            }
        )
    )
    assert "W-EXEC-BUDGET" in found


def test_the_budget_check_does_not_crash_or_guess_when_k_all_cannot_resolve(write_config):
    """A `{kind: fold, k: all}` whose roster did NOT resolve makes the true
    execution count unknown — not zero and not 1×. This config declares no
    `data.units` at all, so there is no roster to count: the honest answer is to
    report `E-REPL-FOLD-NO-UNITS`/`E-REPL-FOLD-K` and skip the budget check
    rather than fold a guessed 1× into it, which would hide an overrun by a
    factor of the roster size. Kept deliberately — the sibling test below is
    what covers the resolvable case."""
    found = codes(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
                "replication": {"repeats": [{"kind": "fold", "k": "all"}]},
                "limits": {"max_executions": 1},
            }
        )
    )
    assert "W-EXEC-BUDGET" not in found


def test_the_budget_check_fires_for_leave_one_out_against_the_real_roster(write_config, tmp_path):
    """Leave-one-out is the single design `W-EXEC-BUDGET` matters most for
    (`reference.md` § Sweeps and repeats) — and it was the one design that could
    not produce the warning, because `_repeat_total` returned `None` on any
    string count while `_check_replication` had already been threaded a real
    `fold_basis`. A 60-unit roster under `k: all` is 60 executions against a
    budget of 10, and it must warn exactly as `k: 60` does."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id\n" + "\n".join(f"p{i}" for i in range(1, 61)) + "\n"
    )
    overrides = {
        "data.units": {"from": "index.csv", "key": "patient_id"},
        "limits": {"max_executions": 10},
    }
    found_all = messages_by_code(
        write_config({**overrides, "replication": {"repeats": [{"kind": "fold", "k": "all"}]}})
    )
    found_60 = messages_by_code(
        write_config({**overrides, "replication": {"repeats": [{"kind": "fold", "k": 60}]}})
    )
    assert "W-EXEC-BUDGET" in found_all
    assert found_all["W-EXEC-BUDGET"] == found_60["W-EXEC-BUDGET"]
    assert "60 executions exceeds 10" in found_all["W-EXEC-BUDGET"]


def test_the_budget_counts_the_conditions_a_group_axis_expands(write_config):
    """`reference.md` § Validation, *Grid size sane*: conditions are counted over
    every axis the sweep expands, "a group axis included, since a group level is a
    condition that executes like any other". The budget is
    `len(expand(doc)) × repeat_total`, so it inherits that from `expand` — which
    now crosses a group axis into the product — and the number the warning names
    must be the real one, not the parameter-only product it was before.

    `groups` is no longer refused wholesale, but this config declares no
    `allocation` at all (defaulting to `within`) beside a declared group axis,
    so `validate` still collects one finding: `E-DATA-ALLOCATION-WITHIN-ARMS`.
    The exact error set is asserted so no unrelated refusal can be the one
    carrying the config.

    Two controls, and the second must report rather than be silent: the same
    design without the group axis fits under the same budget (so the two levels
    are what pushed it over), and at a budget of 10 it warns with *its* count
    (so a silent control cannot be silence from a dead check)."""
    grid = {"analysis.method": ["pearson", "spearman", "kendall"]}
    repeats = {"repeats": [{"kind": "seed", "n": 5}]}
    axis = [{"by": "arm", "levels": ["control", "treatment"]}]

    over = write_config(
        {
            "sweep": {"groups": axis, "grid": grid},
            "replication": repeats,
            "limits": {"max_executions": 20},  # 2 arms × 3 methods × 5 seeds = 30 > 20
        }
    )
    assert _error_codes(over) == {"E-DATA-ALLOCATION-WITHIN-ARMS"}
    assert (
        messages_by_code(over)["W-EXEC-BUDGET"]
        == "6 conditions × 5 repeats = 30 executions exceeds 20"
    )

    without = messages_by_code(
        write_config(
            {"sweep": {"grid": grid}, "replication": repeats, "limits": {"max_executions": 20}}
        )
    )
    assert "W-EXEC-BUDGET" not in without  # 3 × 5 = 15 ≤ 20

    without_tighter = messages_by_code(
        write_config(
            {"sweep": {"grid": grid}, "replication": repeats, "limits": {"max_executions": 10}}
        )
    )
    assert without_tighter["W-EXEC-BUDGET"] == "3 conditions × 5 repeats = 15 executions exceeds 10"


def test_the_floor_warning_also_resolves_k_all_against_the_roster():
    """`W-REPL-FLOOR` was suppressed by the same unresolved-fold flag, so a
    `k: all` over a small roster never warned below the convention floor. It is
    checked here rather than through `validate_config` because `generic`'s
    `default_repeats` is 1, which no positive count can fall below — the floor
    only has a value to compare against under a template that sets one."""
    from publishable.templates.builtin.generic import GenericTemplate
    from publishable.validate import _check_replication

    class ThreeRepeats(GenericTemplate):  # type: ignore[misc]
        default_repeats = 3

    doc = {"replication": {"repeats": [{"kind": "fold", "k": "all"}]}}
    resolved = Collector()
    _check_replication(doc, ThreeRepeats(), resolved, fold_basis=2)
    assert "W-REPL-FLOOR" in {f.code for f in resolved.findings}

    # ...and still silent when the roster genuinely could not resolve.
    unresolved = Collector()
    _check_replication(doc, ThreeRepeats(), unresolved, fold_basis=None)
    assert "W-REPL-FLOOR" not in {f.code for f in unresolved.findings}


def test_a_fold_declaring_n_is_refused_rather_than_read_two_ways(write_config, tmp_path):
    """`{kind: fold, k: 2, n: 5}` validated clean, the budget reported five
    executions, and the run executed two folds. `reference.md` § Repeat kinds
    gives each kind its own fields and only these, so the count field the kind
    does not take is refused rather than resolved by precedence — silently
    preferring one reading is what hid the disagreement."""
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\np2\np3\np4\n")
    found = messages_by_code(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "replication": {"repeats": [{"kind": "fold", "k": 2, "n": 5}]},
                "limits": {"max_executions": 3},
            }
        )
    )
    assert "E-REPL-LEVEL-FIELD" in found
    assert "`n: 5`" in found["E-REPL-LEVEL-FIELD"]
    # and the budget arithmetic no longer believes the ignored count: two folds
    # against a budget of three is under it, where `n: 5` would have warned.
    assert "W-EXEC-BUDGET" not in found


def test_a_seed_declaring_k_is_refused_the_same_way(write_config):
    """The mirror: `k` is a fold's field, and a `seed` carrying one had it
    silently accepted and ignored."""
    found = messages_by_code(
        write_config({"replication": {"repeats": [{"kind": "seed", "n": 2, "k": 9}]}})
    )
    assert "E-REPL-LEVEL-FIELD" in found
    assert "`k: 9`" in found["E-REPL-LEVEL-FIELD"]

    # and the `batch` half, which `reference.md` § Validation has listed as a
    # check ("Batch takes no fields — `{kind: batch, k: 3}`") since before
    # anything enforced it
    assert "E-REPL-LEVEL-FIELD" in codes(
        write_config({"replication": {"repeats": [{"kind": "batch", "k": 3}]}})
    )


def test_a_multi_condition_sweep_warns_about_the_uncorrected_family(write_config):
    """A grid-only sweep with no `sweep.baseline` publishes no baseline
    comparison, so the retired formula `max(len(conditions) - 1, 0) + declared`
    and the current `len(resolve_contrasts(doc, conditions))` disagree here: two
    grid conditions and one declared contrast between them give the old formula
    `(2 - 1) + 1 = 2` and the new one exactly `1` (the declared contrast alone —
    there is no baseline to compare against). A fixture where both formulas
    agree — such as one with a real `sweep.baseline` — would pass even if the
    recount reverted to the retired formula, which is what made the previous
    version of this test lose its discriminating power."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["spearman", "kendall"]}},
                "statistics": {
                    "correction": "none",
                    "contrasts": [
                        {"id": "x", "of": "method=spearman", "against": "method=kendall"}
                    ],
                },
            }
        ),
        c,
    )
    warning = next(f for f in c.findings if f.code == "W-STATS-FAMILY")
    assert "1 comparisons per metric form a family" in warning.message


def test_a_single_condition_run_has_no_family(write_config):
    assert "W-STATS-FAMILY" not in codes(write_config())


def test_warnings_alone_leave_the_exit_code_at_zero(write_config):
    c = Collector()
    validate_config(
        write_config({"sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}}}), c
    )
    assert not c.has_errors
    assert c.exit_code() == 0


def test_an_unexpected_error_finding_the_repo_root_is_not_swallowed(write_config, monkeypatch):
    """`_check_data`'s repo-root lookup narrows its exception handling to the one case
    that legitimately means 'the inside-the-repo question does not arise' — anything
    else must propagate rather than presenting a safety check as a clean pass."""
    import publishable.validate as validate_mod

    def _boom(path):
        raise RuntimeError("disk fell off")

    monkeypatch.setattr(validate_mod, "find_repo_root", _boom)
    with pytest.raises(RuntimeError):
        validate_config(write_config(), Collector())


def test_a_contract_error_other_than_no_repo_is_not_swallowed(write_config, monkeypatch):
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _boom(path):
        raise ContractError("something else went wrong", code="E-SOMETHING-ELSE")

    monkeypatch.setattr(validate_mod, "find_repo_root", _boom)
    with pytest.raises(ContractError):
        validate_config(write_config(), Collector())


def test_the_genuine_no_repo_case_returns_quietly(write_config, monkeypatch):
    """The one case the narrowed handler is for: no repo at all is not a data-in-repo
    problem, so it must return without a spurious finding rather than propagating."""
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _no_repo(path):
        raise ContractError("no git repository found", code="E-GIT-NO-REPO")

    monkeypatch.setattr(validate_mod, "find_repo_root", _no_repo)
    assert codes(write_config()) == set()


def test_the_policy_check_still_runs_with_no_repo_at_all(write_config, monkeypatch):
    """`input_manifest_policy` has nothing to do with the repo, so it must not be
    gated behind the repo-existence early-return `_check_data` takes for the
    in-repo-only checks."""
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _no_repo(path):
        raise ContractError("no git repository found", code="E-GIT-NO-REPO")

    monkeypatch.setattr(validate_mod, "find_repo_root", _no_repo)
    codes_found = codes(write_config({"data.input_manifest_policy": "bogus"}))
    assert "E-DATA-POLICY" in codes_found


def test_a_config_that_does_not_parse_is_fatal(git_repo: Path):
    path = git_repo / "configs" / "cohort-pilot" / "config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("metadata: [unbalanced\n")
    assert "E-CONFIG-PARSE" in codes(path)


def test_a_required_data_dir_left_empty_is_reported(write_config):
    c = Collector()
    validate_config(write_config({"data.output_dir": ""}), c)
    found = [f for f in c.findings if f.code == "E-DATA-REQUIRED"]
    assert len(found) == 1
    assert found[0].path == "data.output_dir"


def test_a_relative_input_dir_is_rejected(write_config):
    assert "E-DATA-NOT-ABSOLUTE" in codes(write_config({"data.input_dir": "./secret"}))


def test_a_relative_output_dir_is_rejected(write_config):
    assert "E-DATA-NOT-ABSOLUTE" in codes(write_config({"data.output_dir": "results"}))


def test_a_missing_data_dir_is_reported_even_outside_any_repo(write_config, monkeypatch):
    """The previous fix wave hoisted `E-DATA-IN-REPO`'s policy check above the
    repo-existence early return but left `E-DATA-REQUIRED` and `E-DATA-UNREADABLE`
    behind it under identical reasoning — neither has anything to do with the repo
    either, so a repo-less config missing `input_dir` must still be caught."""
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _no_repo(path):
        raise ContractError("no git repository found", code="E-GIT-NO-REPO")

    monkeypatch.setattr(validate_mod, "find_repo_root", _no_repo)
    found = codes(write_config({"data.input_dir": _DELETE}))
    assert "E-DATA-REQUIRED" in found


def _with_doc_change(write_config, change) -> Path:
    """Set a top-level key the base fixture does not declare at all — the dotted
    override helper needs the parent key to preexist, which `sweep` and
    `data.units` deliberately do not in the base fixture."""
    path = write_config()
    doc = yaml.safe_load(path.read_text())
    change(doc)
    path.write_text(yaml.safe_dump(doc))
    return path


def test_baseline_and_grid_are_now_accepted(write_config):
    """S3a implements `baseline` and `grid` expansion; a config declaring only
    those must validate clean rather than tripping any sweep refusal."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman"]},
                }
            }
        )
    )
    assert not [c for c in found if c.startswith("E-SWEEP")]


def test_groups_is_accepted_and_expands_for_real(write_config):
    """Task 17 retires `E-SWEEP-GROUPS-UNSUPPORTED`: `groups` is an axis-shaped
    mode `_axes` composes like any other, and a bare declaration no longer
    trips that refusal — `paired`, `sample` and `ablate` lost the same
    refusal earlier, see `test_paired_is_accepted_and_expands_for_real`,
    `test_sample_is_accepted_and_expands_for_real` and
    `test_ablate_is_accepted_and_expands_for_real` below.

    This declares no `allocation`, so `allocation` defaults to `within` beside
    a declared group axis — the mirror fault, `E-DATA-ALLOCATION-WITHIN-ARMS`,
    from `_check_assign` rather than `_check_unimplemented`. It is not an
    `E-SWEEP` code, so asserting no `E-SWEEP`-prefixed finding remains is the
    control that isolates this from that other, already-tested family
    (`test_within_allocation_with_a_group_axis_is_arms_need_allocation`)."""
    found = codes(write_config({"sweep": {"groups": [{"by": "arm", "levels": ["a", "b"]}]}}))
    assert "E-SWEEP-GROUPS-UNSUPPORTED" not in found
    assert not [c for c in found if c.startswith("E-SWEEP")]


def test_paired_is_accepted_and_expands_for_real(write_config):
    """§ Expansion modes retires `E-SWEEP-PAIRED-UNSUPPORTED`: `paired` is now one
    of the axis-shaped modes `_axes` composes, and a config declaring it validates
    clean — `ablate`, `sample`, and `groups` each lost their own such refusal too,
    across earlier tasks and this one."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.method": ["pearson", "spearman"]},
                    "paired": [
                        {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                        {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                    ],
                }
            }
        )
    )
    assert "E-SWEEP-PAIRED-UNSUPPORTED" not in found
    assert not [c for c in found if c.startswith("E-SWEEP")]


def test_sample_is_accepted_and_expands_for_real(write_config):
    """§ Expansion modes retires `E-SWEEP-SAMPLE-UNSUPPORTED`: `sample` is one of
    the axis-shaped modes `_axes` composes, drawing `n` conditions over the
    declared ranges, and a config declaring it validates clean."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "sample": {
                        "n": 8,
                        "method": "sobol",
                        "seed": "auto",
                        "ranges": {
                            "analysis.confidence": {"uniform": [0.80, 0.99]},
                            "analysis.min_samples": {"int_uniform": [10, 200]},
                        },
                    }
                }
            }
        )
    )
    assert "E-SWEEP-SAMPLE-UNSUPPORTED" not in found
    assert not [c for c in found if c.startswith("E-SWEEP")]


def test_ablate_is_accepted_and_expands_for_real(write_config):
    """§ Expansion modes retires `E-SWEEP-ABLATE-UNSUPPORTED`: `ablate` is the one
    mode that does not multiply, applied after the product and reading the
    baseline rather than re-emitting it, and a config declaring it validates
    clean — `groups` lost its own such refusal too, in this task."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson", "analysis.drop_missing": True},
                    "ablate": {
                        "from": "baseline",
                        "remove": ["analysis.drop_missing"],
                        "override": [{"analysis.method": "spearman"}],
                    },
                }
            }
        )
    )
    assert "E-SWEEP-ABLATE-UNSUPPORTED" not in found
    assert not [c for c in found if c.startswith("E-SWEEP")]


def test_an_ablate_override_value_is_checked_against_its_own_param(write_config):
    """An `override` entry is structurally a `grid` value — user-written, planted
    into a condition's config and rendered into its label — so it goes through the
    same `Param.check` on the same identifier. Unchecked, the condition would run
    a value § Validation's "Choices" row promises to refuse."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "ablate": {"override": [{"analysis.method": "pearsonn"}]},
                }
            }
        ),
        c,
    )
    finding = next(f for f in c.findings if f.code == "E-PARAM-VALUE")
    assert finding.path == "sweep.ablate.override[0].analysis.method"


def test_an_ablate_override_path_the_template_does_not_declare_is_refused(write_config):
    """Gated on `_path_resolves` before `_value_checks` indexes `spec[path]`, the
    same order `grid` and `sample` use — otherwise an unknown path is a `KeyError`
    inside a function contracted never to raise."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "ablate": {"override": [{"analysis.methdo": "spearman"}]},
                }
            }
        )
    )
    assert "E-SWEEP-PATH-UNKNOWN" in found
    assert "E-PARAM-VALUE" not in found


def test_an_ablate_remove_path_the_template_does_not_declare_is_refused(write_config):
    """A `remove` path is planted into a condition's config exactly as an
    `override` path is — `expand` sets `false`/`null` at it — so a misspelling
    creates a parameter the template never declared and runs a condition whose
    label claims a change nothing made. Same identifier as `grid`, `baseline`
    and `override` get; the *value* `remove` produces is § Validation's
    "Ablation targets" row, checked separately as `E-SWEEP-ABLATE-TARGET` and
    gated behind this one, since an unknown path has no `Param` to ask."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "ablate": {"remove": ["analysis.methdo"]},
                }
            }
        ),
        c,
    )
    finding = next(f for f in c.findings if f.code == "E-SWEEP-PATH-UNKNOWN")
    assert finding.path == "sweep.ablate.remove[0]"


def test_an_ablate_override_value_carrying_the_axis_separator_is_refused(write_config):
    """Unlike a `baseline` value, an `override` value IS rendered into the label,
    so it takes the nameability check too: a value containing `__` makes a label
    that cannot be parsed back into axes, and a label is also a selector."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "ablate": {"override": [{"analysis.method": "a__b"}]},
                }
            }
        )
    )
    assert "E-SWEEP-VALUE-UNNAMEABLE" in found


def _error_codes(path: Path) -> set[str]:
    """Every ERROR code, warnings excluded.

    The composition tests below assert an exact set rather than membership: both
    started life asserting only that *some* error was reported, and on the first
    draft of the crossed one a since-retired refusal on the config's `baseline`
    fired for an unrelated reason and the loose assertion accepted it. An exact
    set is what proves the refusal under test is the one carrying the config.
    """
    c = Collector()
    validate_config(path, c)
    return {f.code for f in c.findings if f.level == "error"}


def test_ablate_without_a_baseline_is_refused(write_config):
    """§ Expansion modes: `ablate` "reads the baseline rather than re-emitting it
    … It therefore **requires** `sweep.baseline`, which `validate` checks".
    Unrefused it expands to n conditions each carrying only its own change and no
    baseline row at all — a design the specification says cannot exist."""
    found = _error_codes(
        write_config({"sweep": {"ablate": {"remove": ["analysis.drop_missing"]}}})
    )
    # Exactly one error: `E-SWEEP-ABLATE-TARGET`'s baseline branch is gated on a
    # declared baseline precisely so this config reports its one fault once.
    assert found == {"E-SWEEP-ABLATE-BASELINE-MISSING"}


def test_ablate_crossed_with_a_parameter_axis_is_refused(write_config):
    """§ Expansion modes: "the product of 'vary one thing at a time' with a second
    parameter axis is no longer one thing at a time, and there is no defensible
    reading of what it would mean". Unrefused it expands to the baseline, the
    grid's rows, and the ablate rows. `E-SWEEP-PATH-DUPLICATE` does not catch it
    either: ablated paths deliberately do not join the axis-shaped modes' set."""
    found = _error_codes(
        write_config(
            {
                "sweep": {
                    # The baseline fixes the grid axis too. It no longer has to
                    # — a baseline leaving an axis free is legal now — but the
                    # config is kept as written so the exact-set assertion below
                    # still proves `ablate`'s composition is the only fault.
                    "baseline": {
                        "analysis.method": "pearson",
                        "analysis.drop_missing": True,
                        "analysis.min_samples": 30,
                    },
                    "grid": {"analysis.min_samples": [30, 50]},
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        )
    )
    assert found == {"E-SWEEP-ABLATE-CROSSED"}


@pytest.mark.parametrize("mode", ["grid", "paired", "sample"])
def test_ablate_is_refused_against_every_axis_shaped_mode(write_config, mode):
    """The rule names no mode — "a second parameter axis" — so the check reads
    `sweep.PARAMETER_AXIS_MODES` and every member of it is pinned here rather
    than the one § Validation's row happens to illustrate.

    This half cannot discriminate the two predicates on its own: each of these
    is both a product mode and a parameter axis, so the refusal holds either
    way. `test_ablate_composes_with_a_group_axis` below is the discriminator."""
    axis = {
        "grid": {"analysis.method": ["pearson", "spearman"]},
        "paired": [{"analysis.method": "pearson"}, {"analysis.method": "spearman"}],
        "sample": {
            "n": 2,
            "seed": 7,
            "ranges": {"analysis.confidence": {"uniform": [0.9, 0.99]}},
        },
    }[mode]
    found = _error_codes(
        write_config(
            {
                "sweep": {
                    "baseline": {
                        "analysis.method": "pearson",
                        "analysis.confidence": 0.95,
                        "analysis.drop_missing": True,
                    },
                    mode: axis,
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        )
    )
    assert "E-SWEEP-ABLATE-CROSSED" in found


def test_ablate_composes_with_a_group_axis(write_config):
    """§ Validation, "Ablation doesn't compose with a parameter axis": "`groups`
    is permitted — it varies no parameter". Without this, a mutation putting
    `groups` into `PARAMETER_AXIS_MODES` — the set `E-SWEEP-ABLATE-CROSSED`
    reads — passes every other test: this is the one assertion that tells the
    product predicate and the parameter-axis predicate apart. `groups` is no
    longer refused on its own identifier, but — since no `allocation` is
    declared beside it, defaulting to `within` — *Arms need allocation* fires;
    that is the only error this config may carry."""
    found = _error_codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.drop_missing": True},
                    "groups": [{"by": "cohort", "levels": ["derivation", "validation"]}],
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        )
    )
    assert found == {"E-DATA-ALLOCATION-WITHIN-ARMS"}


def test_ablate_times_groups_gives_one_baseline_and_its_ablations_per_level(write_config):
    """§ Expansion modes' own worked example, expanded for real now that H2's
    review could not reach it (`groups` drew `E-SWEEP-GROUPS-UNSUPPORTED`
    wholesale): 2 levels × (1 baseline + 2 ablations) = 6 conditions — the
    document's own arithmetic, not the 2 × 4 = 8 this task's brief first
    proposed and the addendum withdrew, because 8 does not discriminate `(1 + n)
    × levels` from `n × levels` (4 × 2) the way 6 does.

    Run through `expand` directly, on the document's own YAML verbatim (`cohort`
    / `derivation`/`validation`, `features.labs`/`features.notes`) rather than
    through `validate_config` — `GenericTemplate.parameter_spec` declares only
    the four `analysis.*` paths, and `features.*` resolves nowhere in it, so a
    validate-clean run of this exact example is impossible with this template.
    `test_ablate_times_groups_with_declared_paths_validates_clean` below is the
    validate-clean half, expressed against paths this template actually has.

    **The count alone cannot tell a correct expansion from one that emitted the
    baseline once per run instead of once per level** — both give six rows if
    the wrong one also duplicates an ablation — so every label is asserted, as
    a set (six distinct cells, no duplicate, no missing one) rather than a
    length check on its own.

    **`expand`'s actual index order does not match this same section's Index
    row**, which numbers this exact example `00_cohort=derivation__baseline` and
    `03_cohort=validation__baseline` (each cell's baseline at its own head).
    `expand`'s own docstring records why: it emits every baseline row as one
    leading block, then every ablation after it, because "the head of each
    cell" is undefined once a second axis makes a cell's rows non-contiguous —
    a known, already-recorded divergence (`docs/superpowers/spec-defects.md` §
    Per-cell baseline numbering, "Owner: the groups slice", left as a document
    decision rather than a code change taken in passing). Left unasserted here
    on purpose, per review: pinning the leading-block order would entrench a
    divergence from a normative document for no gain this task's own
    assertions don't already cover — "one baseline per level, not per run" is
    carried by the label set above and by `derivation_baseline.index !=
    validation_baseline.index` below, neither of which depends on which index
    order produced them."""
    doc = {
        "sweep": {
            "groups": [{"by": "cohort", "levels": ["derivation", "validation"]}],
            "baseline": {"features.labs": True, "features.notes": True},
            "ablate": {"from": "baseline", "remove": ["features.labs", "features.notes"]},
        }
    }
    conditions = expand(doc)
    assert len(conditions) == 6
    assert {c.label for c in conditions} == {
        "cohort=derivation__baseline",
        "cohort=derivation__labs=false",
        "cohort=derivation__notes=false",
        "cohort=validation__baseline",
        "cohort=validation__labs=false",
        "cohort=validation__notes=false",
    }
    # § Expansion modes' next two claims, pinned beside the count so a change to
    # either doesn't only surface as a stray label somewhere in the six above.
    derivation_baseline = next(
        c for c in conditions if c.label == "cohort=derivation__baseline"
    )
    validation_baseline = next(
        c for c in conditions if c.label == "cohort=validation__baseline"
    )
    assert derivation_baseline.values["features.labs"] is True
    assert validation_baseline.values["features.labs"] is True
    assert derivation_baseline.index != validation_baseline.index  # one baseline PER LEVEL

    # `sweep.baseline` may not name the group axis itself while `ablate` is
    # declared (`E-SWEEP-ABLATE-BASELINE-GROUP`, task 6) — a one-line control
    # that the refusal beside this composition still fires, not duplicated here.
    assert "E-SWEEP-ABLATE-BASELINE-GROUP" in _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": [{"by": "cohort", "levels": ["derivation", "validation"]}],
                    "baseline": {"cohort": "derivation", "analysis.drop_missing": True},
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        )
    )


def test_ablate_times_groups_with_declared_paths_validates_clean(write_config):
    """The validate-clean half of the composition above, against paths
    `GenericTemplate.parameter_spec` actually declares (only `analysis.drop_missing`
    is boolean, so this shape is 2 levels × (1 baseline + 1 ablation) = 4 — a
    different count from the arithmetic test above on purpose, so the two are
    never confused for restating one another). No `allocation` is declared
    beside the axis, so *Arms need allocation* is the one finding this
    well-formed composition may still carry — an empty set here would mean the
    fixture accidentally validates as something other than the plain
    `groups`-with-no-allocation case every other control in this module uses."""
    found = _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": [{"by": "cohort", "levels": ["a", "b"]}],
                    "baseline": {"analysis.drop_missing": True},
                    "ablate": {"from": "baseline", "remove": ["analysis.drop_missing"]},
                }
            }
        )
    )
    assert found == {"E-DATA-ALLOCATION-WITHIN-ARMS"}
    conditions = expand(
        {
            "sweep": {
                "groups": [{"by": "cohort", "levels": ["a", "b"]}],
                "baseline": {"analysis.drop_missing": True},
                "ablate": {"from": "baseline", "remove": ["analysis.drop_missing"]},
            }
        }
    )
    assert len(conditions) == 4


def test_a_plain_ablation_validates_clean(write_config):
    """The legal composition, so that a check firing where it should not fails
    here: a baseline fixing the removed boolean, one `remove`, no axis."""
    assert (
        _error_codes(
            write_config(
                {
                    "sweep": {
                        "baseline": {"analysis.drop_missing": True},
                        "ablate": {"remove": ["analysis.drop_missing"]},
                    }
                }
            )
        )
        == set()
    )


def test_removing_a_parameter_that_is_neither_boolean_nor_nullable_is_refused(
    write_config,
):
    """§ Validation, "Ablation targets", verbatim: "`sweep.ablate.remove[0]` is
    `analysis.min_samples` (int); `remove` needs a boolean or nullable parameter
    — use `override`". A fact about the parameter alone, so it fires even though
    the baseline fixes the path."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.min_samples": 30},
                    "ablate": {"remove": ["analysis.min_samples"]},
                }
            }
        ),
        c,
    )
    finding = next(f for f in c.findings if f.code == "E-SWEEP-ABLATE-TARGET")
    assert finding.path == "sweep.ablate.remove[0]"
    assert "neither a boolean nor nullable" in finding.message
    assert "use `override`" in finding.message


def test_removing_a_nullable_parameter_is_accepted(write_config):
    """The other half of the row: a *nullable* parameter is a legal `remove`
    target even though it is not a boolean. `generic` declares none, so the spec
    is patched for the duration — without this, deleting `or param.nullable`
    from the check fails no test at all."""
    from publishable.param import Param
    from publishable.templates.builtin.generic import GenericTemplate

    original = GenericTemplate.parameter_spec
    GenericTemplate.parameter_spec = {
        **original,
        "analysis.tag": Param(str, default="a", nullable=True),
    }
    try:
        found = _error_codes(
            write_config(
                {
                    "parameters": {"analysis": {"tag": "a"}},
                    "sweep": {
                        "baseline": {"analysis.tag": "a"},
                        "ablate": {"remove": ["analysis.tag"]},
                    },
                }
            )
        )
    finally:
        GenericTemplate.parameter_spec = original
    assert found == set()


def test_removing_a_boolean_the_baseline_leaves_free_is_refused(write_config):
    """The coupling task 4 created: `sweep.removal_value` picks `false` versus
    `null` from the baseline, having no `parameter_spec` to ask, so a boolean the
    baseline does not fix takes the nullable reading and plants `null` at a
    parameter that cannot hold it. The declaration is legal — it IS a boolean —
    and only the produced value shows the fault."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        ),
        c,
    )
    finding = next(f for f in c.findings if f.code == "E-SWEEP-ABLATE-TARGET")
    assert finding.path == "sweep.ablate.remove[0]"
    assert "fixes no *boolean* value for" in finding.message
    assert "null" in finding.message


def test_a_non_boolean_baseline_value_is_not_a_boolean_the_remove_can_turn_off(
    write_config,
):
    """The baseline *does* fix a value here — it is just not a boolean, so
    `removal_value` still takes the `null` reading. The condition branch 2 states
    is "no boolean value", not "no value", and this is the config that tells the
    two apart."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.drop_missing": "yes"},
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        ),
        c,
    )
    finding = next(f for f in c.findings if f.code == "E-SWEEP-ABLATE-TARGET")
    assert "fixes no *boolean* value for" in finding.message


@pytest.mark.parametrize(
    "ablate",
    [
        "notamapping",
        ["notamapping"],
        {"remove": "analysis.drop_missing"},
        {"remove": {"analysis.drop_missing": True}},
        {"remove": [123]},
        {"remove": [["analysis.drop_missing"]]},
        {"override": {"analysis.method": "spearman"}},
        {"override": "analysis.method"},
        {"override": [None]},
        {"override": ["analysis.method"]},
        {"override": [{123: "spearman"}]},
    ],
)
def test_a_misshapen_ablate_is_refused_as_a_shape_fault(write_config, ablate):
    """The class, not the inputs: every type `ablation_changes` would iterate, use
    as a dict key or feed into `_keys_for`'s `.split(".")` is guarded in
    `_check_shape`, fatally, exactly as `grid`, `paired` and `sample` are —
    `validate` swallows expansion crashes, so a shape that makes `expand` raise
    must never reach it."""
    assert "E-CONFIG-SHAPE" in codes(write_config({"sweep": {"ablate": ablate}}))


def test_every_misshapen_ablate_really_does_break_expand():
    """The other half of the guard's claim, asserted rather than argued. Each
    shape above breaks `expand` in one of the two documented ways: a bare
    exception out of a function `validate` calls inside a bare `except`, or —
    for a string where a list belongs — the quiet failure `grid`'s own axis
    guard closed, iterating character by character into one condition per letter.
    `remove: [123]` is the one that raises late, inside `_keys_for`'s
    `.split(".")`, which is why the guard is at the path level and not only at
    the list level."""
    from publishable.sweep import expand

    def _expand(ablate):
        return expand({"sweep": {"baseline": {"analysis.method": "pearson"}, "ablate": ablate}})

    for ablate in (
        {"remove": [123]},
        {"remove": [["analysis.drop_missing"]]},
        {"override": [None]},
        {"override": ["analysis.method"]},
        {"override": [{123: "spearman"}]},
        {"override": "analysis.method"},
    ):
        with pytest.raises((TypeError, AttributeError, ValueError)):
            _expand(ablate)

    # `remove` is the one that fails quietly rather than loudly: one condition
    # per letter of `analysis.drop_missing`, plus the baseline — legal-looking
    # output for a design nobody declared, which is why a string is refused as a
    # shape fault rather than left to expand.
    assert len(_expand({"remove": "analysis.drop_missing"})) == len("analysis.drop_missing") + 1


def test_a_sample_range_bound_outside_its_parameters_constraint_is_refused(write_config):
    """§ Validation, "Sample ranges": `sweep.sample.ranges.analysis.confidence`
    upper bound 1.4 violates the parameter's `lt=1`. The bound is checked with
    the parameter's own `Param`, so it reports `E-PARAM-VALUE` like every other
    illegal value rather than minting a code for the same question."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "sample": {
                        "n": 4,
                        "ranges": {"analysis.confidence": {"uniform": [0.80, 1.4]}},
                    }
                }
            }
        ),
        c,
    )
    found = [f for f in c.findings if f.code == "E-PARAM-VALUE"]
    assert found
    assert found[0].path == "sweep.sample.ranges.analysis.confidence.uniform[1]"
    assert "< 1" in found[0].message


def test_a_sample_range_on_an_undeclared_path_is_refused(write_config):
    """The same `E-SWEEP-PATH-UNKNOWN` a `grid` axis gets — a sampled path is a
    parameter path, and a typo there draws 40 conditions over a parameter the
    template has never heard of."""
    c = Collector()
    validate_config(
        write_config(
            {"sweep": {"sample": {"n": 4, "ranges": {"analysis.confidenc": {"uniform": [0, 1]}}}}}
        ),
        c,
    )
    found = [f for f in c.findings if f.code == "E-SWEEP-PATH-UNKNOWN"]
    assert found
    assert found[0].path == "sweep.sample.ranges.analysis.confidenc"


@pytest.mark.parametrize(
    "sample",
    [
        {"ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}}},
        {"n": 0, "ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}}},
        {"n": 4},
        {"n": 4, "ranges": {}},
        {"n": 4, "ranges": {"analysis.confidence": {}}},
        {"n": 4, "ranges": {"analysis.confidence": {"gaussian": [0.8, 0.99]}}},
        {"n": 4, "ranges": {"analysis.confidence": {"uniform": [0.99, 0.8]}}},
        {"n": 4, "ranges": {"analysis.confidence": {"log_uniform": [0, 0.99]}}},
        {"n": 4, "method": "gaussian", "ranges": {"analysis.confidence": {"uniform": [0, 1]}}},
        {"n": 4, "seed": "17", "ranges": {"analysis.confidence": {"uniform": [0, 1]}}},
    ],
)
def test_a_sample_that_cannot_be_drawn_from_is_refused(write_config, sample):
    """Every value-level fault `sweep.sample` can carry is reported before
    anything executes, under one identifier. `validate` swallows expansion
    crashes on the premise that these checks report them, so a fault reaching
    `expand` unreported is a config that validates clean and crashes `run`."""
    assert "E-SWEEP-SAMPLE-INVALID" in codes(write_config({"sweep": {"sample": sample}}))


@pytest.mark.parametrize(
    "sample",
    [
        "notamapping",
        ["notamapping"],
        {"n": "8", "ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}}},
        {"n": True, "ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}}},
        {"n": 4, "method": ["sobol"], "ranges": {"analysis.confidence": {"uniform": [0, 1]}}},
        {"n": 4, "seed": ["auto"], "ranges": {"analysis.confidence": {"uniform": [0, 1]}}},
        {"n": 4, "ranges": []},
        {"n": 4, "ranges": {123: {"uniform": [0, 1]}}},
        {"n": 4, "ranges": {"analysis.confidence": "uniform"}},
        {"n": 4, "ranges": {"analysis.confidence": {123: [0, 1]}}},
        {"n": 4, "ranges": {"analysis.confidence": {"uniform": 0.5}}},
        {"n": 4, "ranges": {"analysis.confidence": {"uniform": ["0", "1"]}}},
        {"n": 4, "ranges": {"analysis.confidence": {"uniform": [True, False]}}},
    ],
)
def test_a_misshapen_sample_is_refused_as_a_shape_fault(write_config, sample):
    """The class, not the inputs: every type `_sample_cells` would index, split,
    compare or use as a dict key is guarded in `_check_shape`, fatally, exactly
    as `grid` and `paired` are — a YAML-expressible type that makes the drawing
    code raise must not reach it."""
    assert "E-CONFIG-SHAPE" in codes(write_config({"sweep": {"sample": sample}}))


def test_a_sample_path_shared_with_grid_is_refused(write_config):
    """`sample` joins the same product `grid` and `paired` do, so a path written
    by two axis-shaped modes is the same silent overwrite — worse here, since
    `sweep.yaml` records the drawn value as the condition's while the run used
    the `grid` cell's."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.min_samples": [30, 50]},
                    "sample": {
                        "n": 4,
                        "ranges": {"analysis.min_samples": {"int_uniform": [10, 200]}},
                    },
                }
            }
        ),
        c,
    )
    found = [f for f in c.findings if f.code == "E-SWEEP-PATH-DUPLICATE"]
    assert found
    assert found[0].path == "sweep.sample.analysis.min_samples"
    assert "sweep.grid.analysis.min_samples" in found[0].message


def test_grid_and_paired_naming_the_same_path_is_refused(write_config):
    """`expand`'s product applies each axis's cell to `values` in order, so a
    path named by both `grid` and `paired` lets whichever mode is later silently
    overwrite the other's value on every combination — collapsing two of the
    four combinations to byte-identical `values` (grid=30/paired-30 and
    grid=50/paired-30 both resolve to `min_samples=30`). Filed as a spec gap
    (`docs/superpowers/spec-defects.md`) and refused rather than executed."""
    path = write_config(
        {
            "sweep": {
                "grid": {"analysis.min_samples": [30, 50]},
                "paired": [
                    {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                    {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                ],
            }
        }
    )
    c = Collector()
    validate_config(path, c)
    found = [f for f in c.findings if f.code == "E-SWEEP-PATH-DUPLICATE"]
    assert found
    assert found[0].path == "sweep.paired.analysis.min_samples"


def test_grid_and_paired_on_disjoint_paths_is_not_a_duplicate(write_config):
    """The mirror case: `grid` and `paired` naming different paths is exactly
    the brief's own worked example and must stay clean."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.method": ["pearson", "spearman"]},
                    "paired": [
                        {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                        {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                    ],
                }
            }
        )
    )
    assert "E-SWEEP-PATH-DUPLICATE" not in found


def test_an_empty_or_null_mode_is_not_a_declaration(write_config):
    """`init` may write these absent or null; only a truthy value is refused."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.method": ["spearman"]},
                    "paired": [],
                    "ablate": None,
                    "sample": None,
                    "groups": [],
                }
            }
        )
    )
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


def test_randomized_replication_order_validates_clean(write_config):
    """`as_declared` and `randomized` both ship in this build — neither is refused."""
    found = codes(write_config({"replication.order": "randomized"}))
    assert "E-REPL-ORDER" not in found


def test_a_config_without_unimplemented_blocks_still_validates_clean(write_config):
    """The base fixture declares no sweep axis, no `data.units`, and
    `replication.order: as_declared` — none of the new refusals should fire
    against it."""
    found = codes(write_config())
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


def test_a_plain_units_block_is_now_accepted(write_config):
    """The blanket refusal is retired: S2 resolves a roster."""
    found = codes(write_config({"data.units": {"from": "index.csv", "key": "patient_id"}}))
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


def test_holdout_is_refused_on_its_own(write_config):
    """`allocation` and `assign` were rows of this same family until task 17
    retired their `-UNSUPPORTED` refusals — `_check_assign` now checks both for
    real, see `test_by_attribute_assignment_is_accepted` and its neighbors.
    `cluster_by` and `weight_by` left the same way earlier: each became a
    declaration core honors — `cluster_by` counts the clusters, keeps one out
    of two folds, and makes every `basis: units` interval cluster-robust;
    `weight_by` computes Kish's effective size and weights every `basis: units`
    column and interval. What either may not yet be combined with is checked by
    `test_a_clustered_generated_comparison_is_refused` and
    `test_a_weighted_generated_comparison_is_refused` below, and, at run time,
    by `test_cli.py`'s `E-DATA-CLUSTER-DERIVED`. `holdout` is the one field
    left in this family — read by nothing yet."""
    units = {
        "from": "index.csv",
        "key": "patient_id",
        "holdout": {"method": "random", "frac": 0.2},
    }
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in codes(write_config({"data.units": units}))


def test_allocation_within_is_accepted_because_it_is_a_no_op_here(write_config):
    units = {"from": "index.csv", "key": "patient_id", "allocation": "within"}
    assert "E-DATA-ALLOCATION-METHOD" not in codes(write_config({"data.units": units}))


def test_an_out_of_enum_allocation_is_refused_by_its_own_check(write_config):
    """The gap `docs/superpowers/spec-defects.md` recorded against task 12:
    once `E-DATA-ALLOCATION-UNSUPPORTED`'s blanket refusal retired, nothing
    else covered a misspelled `allocation` value — `envelope.py` types the
    field a bare `str`, and *Arms need allocation* is deliberately gated to
    `(None, "within")` so it does not misreport a typo as `within`. Task 17
    closes it with `E-DATA-ALLOCATION-METHOD`, checked before either
    `_check_assign` branch runs.

    Two controls, both of which must report: `within` and `between` are each
    in the enum and must not draw this code (the second needs `sweep.groups`
    declared too, or it draws *Allocation needs arms* instead — a different,
    also-correct finding this test is not about)."""
    units = {"from": "index.csv", "key": "patient_id", "allocation": "sideways"}
    found = _error_codes(write_config({"data.units": units}))
    assert found == {"E-DATA-ALLOCATION-METHOD"}
    message = messages_by_code(write_config({"data.units": units}))["E-DATA-ALLOCATION-METHOD"]
    assert "sideways" in message
    assert "within" in message and "between" in message

    assert "E-DATA-ALLOCATION-METHOD" not in _error_codes(
        write_config({"data.units": {"from": "index.csv", "key": "patient_id",
                                      "allocation": "within"}})
    )
    assert "E-DATA-ALLOCATION-METHOD" not in _error_codes(
        write_config(_between({"arm": {"method": "by_attribute"}}, attributes=["arm"]))
    )


def test_a_malformed_groups_entry_is_a_shape_fault(write_config):
    """`sweep.groups` gets the same container/entry walk `grid`/`paired`/`ablate`
    get in `_check_shape` — the debt `validate.py`'s own comment on
    `_check_assign`'s docstring named for the slice that retires
    `E-SWEEP-GROUPS-UNSUPPORTED`. Before this guard, a non-list `groups`, a
    non-mapping entry, or a non-string `by`/level dropped the axis from the
    product with no finding at all; now each is `E-CONFIG-SHAPE`.

    Four shapes, each reported once, and a well-formed axis as the control
    that must NOT report — `_check_shape`'s guard is additive, not a rejection
    of `groups` itself."""
    assert "E-CONFIG-SHAPE" in codes(write_config({"sweep": {"groups": {"by": "arm"}}}))
    assert "E-CONFIG-SHAPE" in codes(write_config({"sweep": {"groups": ["not-a-mapping"]}}))
    assert "E-CONFIG-SHAPE" in codes(
        write_config({"sweep": {"groups": [{"by": 123, "levels": ["a", "b"]}]}})
    )
    assert "E-CONFIG-SHAPE" in codes(
        write_config({"sweep": {"groups": [{"by": "arm", "levels": [1, 2]}]}})
    )
    assert "E-CONFIG-SHAPE" not in codes(
        write_config({"sweep": {"groups": [{"by": "arm", "levels": ["a", "b"]}]}})
    )


def test_a_blank_group_axis_name_is_a_shape_fault(write_config):
    """A `by` of the right *type* and no content is still refused, because it is
    the one shape where `sweep.selector_paths` and `cli._resolved_group_axes`
    disagree over a config a user can actually write.

    `isinstance(by, str)` accepts `""`, so `expand` renders conditions under it
    (`selectors == {""}`, labels `=a`/`=b`) while `_resolved_group_axes`' own
    `not axis` check skips the axis. With no `assign` block of that name the
    mismatch surfaces late as `E-DATA-ASSIGN-MISSING`; *with* one — and
    `data.units.assign` is a bare mapping no schema closes — task 20's probe
    ran this end to end and the config validated clean, then `run` died on
    `units.arm_members`' bare `KeyError('')`: a traceback out of a command
    rather than a diagnostic.

    An all-whitespace name is refused beside it for a different reason: it
    resolves fine, and task 20's probe ran `by: " "` to a green `run.yaml` with
    correctly narrowed arms — but it names condition directories (`00_ =control`)
    that no other path in this project can produce.

    The control is the same well-formed axis the test above uses, plus a `by`
    that merely *contains* a space, which is not this rule's business."""
    for blank in ("", " ", "\t", "\n"):
        assert "E-CONFIG-SHAPE" in codes(
            write_config({"sweep": {"groups": [{"by": blank, "levels": ["a", "b"]}]}})
        ), f"a `by` of {blank!r} was accepted"
    assert "E-CONFIG-SHAPE" not in codes(
        write_config({"sweep": {"groups": [{"by": "arm", "levels": ["a", "b"]}]}})
    )
    assert "E-CONFIG-SHAPE" not in codes(
        write_config({"sweep": {"groups": [{"by": "study arm", "levels": ["a", "b"]}]}})
    )
    # And it does not stop the pass. Unlike every container fault `_check_shape`
    # reports, this one leaves `ok` alone — § Errors `validate` reports frames
    # the early return as a container fault because every later check indexes
    # into a block already known to be the wrong kind, which a well-typed string
    # is not. A blank `by` under `allocation: between` must therefore still earn
    # `E-DATA-ASSIGN-MISSING` in the same pass; returning early would report one
    # finding and hide the rest.
    both = codes(
        write_config(
            {
                "sweep": {"groups": [{"by": "", "levels": ["a", "b"]}]},
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "allocation": "between",
                },
            }
        )
    )
    assert "E-CONFIG-SHAPE" in both
    assert "E-DATA-ASSIGN-MISSING" in both, both


def test_a_group_axis_name_that_renders_blank_is_a_shape_fault(write_config):
    """The rule is about the axis name **as `label_for` renders it**, not about
    `by` whole — `path.rsplit('.', 1)[-1]`.

    A first version of the check above tested `by.strip()`, which left `by:
    "arm."` open: it renders to nothing, and driven end to end with a matching
    `assign` block it produced labels `=control`/`=treatment`, directories
    `00_=control`/`01_=treatment`, and exit 0 with nothing reported — the exact
    outcome the refusal exists to prevent, reached by a `by` that passes
    `strip()`. The rendered name is what a reader sees and what a directory
    carries, so it is what the rule is about.

    `analysis.method` is the control: a dotted `by` whose last segment is a real
    name renders to `method=…` and is nobody's business here."""
    for by in ("arm.", "a.b.", "arm. ", "."):
        assert "E-CONFIG-SHAPE" in codes(
            write_config({"sweep": {"groups": [{"by": by, "levels": ["a", "b"]}]}})
        ), f"a `by` of {by!r} renders blank and was accepted"
    assert "E-CONFIG-SHAPE" not in codes(
        write_config({"sweep": {"groups": [{"by": "cohort.arm", "levels": ["a", "b"]}]}})
    )


def test_the_blank_axis_name_rule_is_an_allowlist_not_a_denylist(write_config):
    """The predicate is `sweep.NAMEABLE_CHAR` — at least one of the class
    `SWEPT_VALUE_PATTERN` is built from — rather than an enumeration of what is
    forbidden, and the invisible codepoints are what force that shape.

    Three spellings of one fault reached a run: `""` and `" "` were caught by a
    `.strip()` predicate, `"arm."` was not (it renders to nothing after the last
    `.`), and a zero-width space is not caught by `.strip()` either — `'\\u200b'
    .isspace()` is False — so `by: "\\u200b"` validated clean and named
    directories `00_\\u200b=control`. A denylist loses this race by construction:
    there is an unbounded supply of invisible codepoints and one alphabet of
    legal ones.

    So this test asserts the *class*, over four invisibles no `.strip()` sees,
    each also in its post-`.` form. The controls are the reason the rule is "at
    least one" rather than `SWEPT_VALUE_PATTERN`'s full match: `study arm` and
    `arm\\xa0` both render, resolve and narrow correctly, and refusing them would
    be a separate rule about label hygiene that nobody has argued for."""
    for ch in ("​", "‌", "﻿", "⁠"):
        for by in (ch, f"arm.{ch}", f"{ch}.{ch}"):
            assert by.rsplit(".", 1)[-1].strip() != "", (
                f"{by!r} is caught by strip(), so it does not discriminate the "
                "allowlist from the denylist it replaced"
            )
            assert "E-CONFIG-SHAPE" in codes(
                write_config({"sweep": {"groups": [{"by": by, "levels": ["a", "b"]}]}})
            ), f"a `by` of {by!r} has no nameable character and was accepted"
    for by in ("arm", "study arm", "arm\xa0", "a", "0", "_x"):
        assert "E-CONFIG-SHAPE" not in codes(
            write_config({"sweep": {"groups": [{"by": by, "levels": ["a", "b"]}]}})
        ), f"a `by` of {by!r} names something and must not be refused"


def test_a_group_axis_repeating_a_level_is_refused(write_config):
    """`E-SWEEP-LEVEL-DUPLICATE` — a route to § Mistakes core prevents' *two
    identical measurements reported as two arms* that no allocation code closes.
    (`E-SWEEP-BASELINE-GROUP` closes the other one, a baseline fixing a level of
    the axis; neither reaches the other's shape.)

    `E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ALLOCATION-WITHIN-ARMS` both read the
    `within`-versus-arms question, and a config with `allocation: between` and a
    real axis satisfies both. `E-SWEEP-PATH-DUPLICATE` compares axis *names*
    across entries, never values inside one entry's `levels`. And `arms_of`'s set
    equality has nothing to disagree with, because `{control} == {control}`.

    Driven end to end before this check existed, `levels: [control, treatment,
    control]` over a roster holding both values ran to exit 0 with `00_arm=control`
    and `02_arm=control` **byte-identical at every artifact**, including every
    seed repeat's `units.parquet` — one measurement reported as two arms, which is
    the row verbatim.

    The two controls matter for different reasons: a distinct pair must not
    report, and a *parameter* axis repeating a value must not either. That
    second one is a deliberate gap, and **not because its consequence is
    milder** — crossed with a group axis it reproduces this outcome exactly,
    `00_arm=control__method=pearson` and `01_arm=control__method=pearson`
    identical at every artifact on exit 0, with duplicated arm-bearing label
    bodies that are selectors. The line is about what a duplicate *means*: a
    group level is a claim about which units, a parameter value is not.
    `E-SWEEP-LEVEL-DUPLICATE`'s registry row records the gap."""
    found = messages_by_code(
        write_config({"sweep": {"groups": [{"by": "arm", "levels": ["c", "t", "c"]}]}})
    )
    assert "E-SWEEP-LEVEL-DUPLICATE" in found
    assert "'c'" in found["E-SWEEP-LEVEL-DUPLICATE"], found["E-SWEEP-LEVEL-DUPLICATE"]
    assert "levels[0]" in found["E-SWEEP-LEVEL-DUPLICATE"]
    assert "E-SWEEP-LEVEL-DUPLICATE" not in codes(
        write_config({"sweep": {"groups": [{"by": "arm", "levels": ["c", "t"]}]}})
    )
    assert "E-SWEEP-LEVEL-DUPLICATE" not in codes(
        write_config({"sweep": {"grid": {"analysis.method": ["pearson", "pearson"]}}})
    )
    # And the crossed case stays unrefused too — pinned so the recorded gap is
    # visible in the suite rather than only in prose. If a later slice closes
    # the parameter-axis duplicate, this assertion is the one that must change,
    # and its failure is the reminder that the registry row says so.
    assert "E-SWEEP-LEVEL-DUPLICATE" not in codes(
        write_config(
            {
                "sweep": {
                    "groups": [{"by": "arm", "levels": ["control", "treatment"]}],
                    "grid": {"analysis.method": ["pearson", "pearson"]},
                }
            }
        )
    )
    # The scope control: `seen` resets per entry, so two DIFFERENT axes sharing a
    # level name is ordinary and must not report. `sex=f × arm=f` is silly but
    # legal, and hoisting the tally out of the per-entry loop — the obvious way
    # to write this wrong — turns every such design into a false refusal.
    assert "E-SWEEP-LEVEL-DUPLICATE" not in codes(
        write_config(
            {
                "sweep": {
                    "groups": [
                        {"by": "sex", "levels": ["f", "m"]},
                        {"by": "arm", "levels": ["f", "t"]},
                    ]
                }
            }
        )
    )


def test_a_resolver_source_is_refused_until_plugins_exist(write_config):
    units = {"from": {"resolver": "plate_wells"}, "key": "well"}
    assert "E-DATA-RESOLVER-UNSUPPORTED" in codes(write_config({"data.units": units}))


@pytest.mark.parametrize(
    "units",
    [
        {"from": {"resolver": "plate_wells"}, "key": "well"},
        {"from": "index.csv", "key": "patient_id", "holdout": {"method": "random", "frac": 0.2}},
    ],
)
def test_every_unsupported_message_defers_rather_than_scolds(write_config, units):
    """The `-UNSUPPORTED` family exists so a refusal reads as 'not built yet', not as
    'your config is wrong'. Every message in this family must say so explicitly, or a
    user has no way to tell a refusal from a validation error. `allocation: between` and
    `assign` were rows here until task 17 retired their `-UNSUPPORTED` refusals — each
    now draws a real, behavior-specific finding instead (`E-DATA-ALLOCATION-NO-ARMS`,
    `E-DATA-ASSIGN-MISSING`, and so on), not a deferral."""
    found = messages_by_code(write_config({"data.units": units}))
    unsupported = {code: msg for code, msg in found.items() if code.endswith("-UNSUPPORTED")}
    assert unsupported, f"expected an -UNSUPPORTED finding for {units}"
    for code, message in unsupported.items():
        assert "later slice" in message, f"{code} message does not defer: {message!r}"


def test_a_null_subfield_is_not_a_declaration(write_config):
    """`init` writes these as null; null must not trip a refusal."""
    units = {
        "from": "index.csv",
        "key": "patient_id",
        "cluster_by": None,
        "weight_by": None,
        "measurements": None,
        "holdout": None,
    }
    found = codes(write_config({"data.units": units}))
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


def test_a_mean_collapse_over_a_string_column_is_refused(write_config, tmp_path):
    """§ Validation, "Collapse rule fits the column". `mean` over `site` has no
    meaning; the row names the remedies."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,site,read_id\np1,north,r1\np2,south,r2\n"
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site", "read_id"],
                "measurements": {"by": "read_id", "collapse": "mean"},
            }
        }
    )
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" in codes(path)


def test_a_per_column_map_sparing_the_string_column_is_accepted(write_config, tmp_path):
    """The remedy the row names must actually work, or the check is a trap."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,site,depth,read_id\np1,north,10,r1\np2,south,20,r2\n"
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site", "depth", "read_id"],
                "measurements": {"by": "read_id", "collapse": {"depth": "mean", "site": "first"}},
            }
        }
    )
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" not in codes(path)


def test_measurements_missing_by_is_refused(write_config):
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "measurements": {"collapse": "mean"},
            }
        }
    )
    assert "E-DATA-MEASUREMENTS-INVALID" in codes(path)


def test_an_empty_measurements_block_is_a_finding_not_a_default(write_config):
    """Decision 3. The truthiness gate that lets `{}` through today is a hole:
    un-refusing a declaration must not turn its empty form into a working default.
    Exactly one finding, at the block's own path — not the `by`-shaped one a
    dict-but-empty `{}` would also earn by falling through to the next check —
    which is what makes this a distinct branch from
    `test_measurements_missing_by_is_refused` rather than the same one reached
    twice."""
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "measurements": {}}}
    )
    c = Collector()
    validate_config(path, c)
    relevant = [
        f
        for f in c.findings
        if f.code.startswith("E-DATA-MEASUREMENTS") or f.code == "E-UNITS-COLLAPSE-RULE"
    ]
    assert {f.code for f in relevant} == {"E-DATA-MEASUREMENTS-INVALID"}
    assert relevant[0].path == "data.units.measurements"


def test_a_constant_string_column_is_refused_despite_surviving_at_run_time(write_config, tmp_path):
    """`units.apply_rule`'s constant-column shortcut would let `mean` over a *constant*
    `site` string survive at run time without ever dispatching to a numeric
    operation. `validate` refuses it anyway: a check whose verdict depends on
    whether the data happened to be constant is one nobody could act on, and the
    document draws no such exception for row 243."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,site,read_id\np1,north,r1\np2,north,r2\n"
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site", "read_id"],
                "measurements": {"by": "read_id", "collapse": "mean"},
            }
        }
    )
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" in codes(path)


def test_sum_over_a_real_boolean_column_is_refused(write_config):
    """A CSV cannot carry a genuine `bool` attribute — `csv.DictReader` yields
    strings — so this exercises the check directly with a hand-built roster, the
    same gate `units.apply_rule` uses (`bool` is excluded from "numeric" even though
    `isinstance(True, int)` is `True`)."""
    roster = UnitList(
        [
            Unit(key="p1", attributes={"flag": True, "read_id": "r1"}),
            Unit(key="p2", attributes={"flag": True, "read_id": "r2"}),
        ]
    )
    c = Collector()
    _check_measurements(
        {"measurements": {"by": "read_id", "collapse": {"flag": "sum"}}},
        roster,
        None,
        frozenset({"flag", "read_id"}),
        c,
    )
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" in {f.code for f in c.findings}


def test_sum_over_a_csv_sourced_boolean_looking_column_is_refused(write_config, tmp_path):
    """The reachable-from-CSV half of the same fault: `"True"`/`"False"` do not
    parse as `float`, so they are refused under a numeric rule the same as any
    other non-numeric string — `bool`-vs-`str` is not a distinction this check
    needs to draw, only numeric-vs-not."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,active,read_id\np1,True,r1\np2,False,r2\n"
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["active", "read_id"],
                "measurements": {"by": "read_id", "collapse": {"active": "sum"}},
            }
        }
    )
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" in codes(path)


def test_a_numeric_looking_csv_string_column_is_accepted_under_mean(write_config, tmp_path):
    """Decision: a table-sourced column arrives as `str` (`csv.DictReader` does no
    coercion, and neither does `resolve_units` yet — that typing is task 3's).
    Treating every table column as non-numeric would refuse `collapse: mean` over
    the ordinary numeric case everywhere it appears. `"10"`/`"20"` parse as
    `float`, so they are accepted; only a value that does NOT parse (`"north"`) is
    refused. **Consequence, not yet closed**: `units.apply_rule`'s `sum`/`median` on
    these same strings raises a bare `TypeError` at run time until task 3 adds the
    coercion this check does not perform — a cross-task gap, not a bug here."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,depth,read_id\np1,10,r1\np2,20,r2\n"
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth", "read_id"],
                "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
            }
        }
    )
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" not in codes(path)


def test_an_unknown_collapse_rule_name_draws_the_shared_collapse_rule_code(write_config):
    """`reference.md` § Errors `validate` reports already dual-lists
    `E-UNITS-COLLAPSE-RULE` for exactly this fault — the same code
    `units.apply_rule` raises once task 3 wires collapse into `resolve_units` — so
    this check reuses it rather than minting a second code (`-INVALID`) for the
    fault `apply_rule` will also raise on, the "one problem, two codes" split
    `_check_units`'s own docstring names as the failure to avoid absent a
    surface-split reason."""
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "measurements": {"by": "read_id", "collapse": "bogus"},
            }
        }
    )
    found = codes(path)
    assert "E-UNITS-COLLAPSE-RULE" in found
    assert "E-DATA-MEASUREMENTS-INVALID" not in found


def test_an_omitted_collapse_draws_invalid_not_the_named_rule_code(write_config):
    """`E-UNITS-COLLAPSE-RULE`'s own row says it fires for a rule that *names*
    something outside `mean`/`median`/`sum`/`first`/`mode` — an omission names
    nothing, so it belongs to the shape family instead. Routing it there also
    keeps `E-UNITS-COLLAPSE-RULE` meaning exactly what both its registry rows
    say, which matters more than usual since it is dual-listed with the code
    `units.apply_rule` itself raises."""
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "measurements": {"by": "read_id"},
            }
        }
    )
    found = codes(path)
    assert "E-DATA-MEASUREMENTS-INVALID" in found
    assert "E-UNITS-COLLAPSE-RULE" not in found


def test_an_empty_collapse_map_defaults_every_column_to_first_and_is_accepted(
    write_config, tmp_path
):
    """A per-column map's un-named column falls back to `first`
    (`units.rule_for`'s own fallback), so an empty map names no column and
    every column takes that fallback — the same declaration as `collapse:
    first` written out for nothing. Pinned as accepted rather than as a second
    empty-mapping refusal: `measurements.collapse: {}` is a coherent (if
    vacuous) per-column map, unlike `measurements: {}` itself, which names
    neither `by` nor `collapse` at all."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,site,read_id\np1,north,r1\np2,south,r2\n"
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site", "read_id"],
                "measurements": {"by": "read_id", "collapse": {}},
            }
        }
    )
    found = codes(path)
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" not in found
    assert "E-UNITS-COLLAPSE-RULE" not in found
    assert "E-DATA-MEASUREMENTS-INVALID" not in found


def test_a_non_string_by_is_reported_rather_than_crashing(write_config):
    """`by` feeds a set difference (`{... for u in roster ...} - {by}`) further
    down the check — a list or dict `by` is unhashable there, so the check must
    normalize a wrongly-typed `by` to something hashable before that point, not
    merely flag it and carry the raw value forward."""
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "measurements": {"by": ["a"], "collapse": "first"},
            }
        }
    )
    found = codes(path)  # must not raise
    assert "E-DATA-MEASUREMENTS-INVALID" in found


def test_the_roster_skip_does_not_swallow_the_shape_check(write_config, tmp_path):
    """When the roster cannot resolve, the type half of the check is skipped — but
    the shape half must still run, or an unreadable `input_dir` becomes a second
    way for a malformed `measurements` block to validate clean."""
    empty_dir = tmp_path / "empty_input"
    empty_dir.mkdir()
    path = write_config(
        {
            "data.input_dir": str(empty_dir),
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "measurements": {"collapse": "mean"},
            },
        }
    )
    found = codes(path)
    assert "E-DATA-UNREADABLE" in found
    assert "E-DATA-MEASUREMENTS-INVALID" in found
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" not in found


def test_a_repeated_key_is_not_a_duplicate_once_measurements_is_declared(write_config, tmp_path):
    """Resolution collapses before it checks uniqueness, and `validate` resolves
    the same roster `run` will — so the repeated key that is the *point* of a
    `measurements` declaration must not also be reported as a defect."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,depth,read_id\np1,10,r1\np1,20,r2\np2,30,r3\n"
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth", "read_id"],
                "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
            }
        }
    )
    found = codes(path)
    assert "E-UNITS-KEY-DUPLICATE" not in found
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" not in found


def test_a_mixed_column_under_mean_is_a_finding_rather_than_an_escaping_type_error(
    write_config, tmp_path
):
    """The invariant this task is most able to break: `validate` collects findings
    and never raises. `_check_units` wraps resolution in `except ContractError`
    only, so the arithmetic the collapse now performs has to refuse with a code —
    a bare `TypeError` out of `sum` would come straight out of `validate_config`.
    `codes(path)` calls it, so this test fails by erroring if that ever regresses."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,depth,read_id\np1,10,r1\np1,north,r2\n"
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth", "read_id"],
                "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
            }
        }
    )
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" in codes(path)


_MEASURED_CSV = (
    # Asymmetric on purpose: mean 30, median 20, sum 90, first 10 all differ, so a
    # rule swapped for another one cannot pass by coincidence.
    "patient_id,depth,read_id\n"
    "p1,10,r1\np1,20,r2\np1,60,r3\n"
    "p2,30,r1\np2,40,r2\np2,80,r3\n"
)


def test_a_measurements_by_naming_no_column_is_refused_when_rows_were_collapsed(
    write_config, tmp_path
):
    """The wrong-answer path retiring `E-DATA-MEASUREMENTS-UNSUPPORTED` would open.

    `units.collapse_measurements` groups on the unit key alone, so a `by` naming
    nothing collapses exactly as a correct one would — and reports a `technical_n`
    claiming the merge was intentional. Rows nothing declared to be measurements of
    one unit, averaged."""
    (tmp_path / "input" / "index.csv").write_text(_MEASURED_CSV)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth", "read_id"],
                "measurements": {"by": "nonexistent", "collapse": {"depth": "mean"}},
            }
        }
    )
    c = Collector()
    validate_config(path, c)
    offending = [f for f in c.findings if f.code == "E-UNITS-ATTR-MISSING"]
    assert offending, {f.code for f in c.findings}
    assert offending[0].path == "data.units.measurements.by"


def test_the_documents_own_fence_shape_is_accepted(write_config, tmp_path):
    """`reference.md` § What isn't a repeat and `experimental-designs.md`
    § Technical and biological replication both print `from`/`key`/`measurements`
    with **no `attributes` key at all**, and `design-principles.md` — the
    tiebreaker — lists `measurements.by` beside `attributes` as a parallel namer of
    an input field rather than a member of it. So `by` naming a real column of the
    source table is the documented shape, and checking it against the declared
    attributes would refuse the document's own example."""
    (tmp_path / "input" / "index.csv").write_text(_MEASURED_CSV)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "measurements": {"by": "read_id", "collapse": "mean"},
            }
        }
    )
    found = codes(path)
    assert "E-UNITS-ATTR-MISSING" not in found
    assert not [c for c in found if c.startswith("E-")], found


def test_a_by_no_column_carries_is_refused_even_with_no_attributes_declared(
    write_config, tmp_path
):
    """The control for the fence test above, and the wrong-answer path itself in
    the shape the documents print: the same config with a typo'd `by`, which names
    no column of `index.csv`, must still be refused."""
    (tmp_path / "input" / "index.csv").write_text(_MEASURED_CSV)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "measurements": {"by": "raed_id", "collapse": "mean"},
            }
        }
    )
    c = Collector()
    validate_config(path, c)
    offending = [f for f in c.findings if f.code == "E-UNITS-ATTR-MISSING"]
    assert offending, {f.code for f in c.findings}
    assert offending[0].path == "data.units.measurements.by"
    assert "index.csv does not have" in offending[0].message


def test_a_by_naming_a_real_column_is_accepted(write_config, tmp_path):
    """The control the refusal needs: the same table, the same collapse, and a `by`
    that names a real column — no finding, or the check refuses every config. Here
    the column is also declared under `attributes`, which is legal and irrelevant:
    the check reads the source's columns, not the declared set."""
    (tmp_path / "input" / "index.csv").write_text(_MEASURED_CSV)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth", "read_id"],
                "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
            }
        }
    )
    found = codes(path)
    assert "E-UNITS-ATTR-MISSING" not in found
    assert not [c for c in found if c.startswith("E-DATA-MEASUREMENTS")]


def test_a_by_no_input_column_carries_is_accepted_when_nothing_was_collapsed(
    write_config, tmp_path
):
    """The step path's `by` names a measurement identity the STEP invents —
    `io.record(unit.key, values, measurement=read_id)` — and no input column
    carries it. `artifacts._collapse_measurements` never reads `by`, and with one
    row per unit the input path merged nothing, so there is no wrong number to
    refuse and refusing would refuse a documented design."""
    (tmp_path / "input" / "index.csv").write_text("patient_id,depth\np1,10\np2,30\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth"],
                "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
            }
        }
    )
    assert "E-UNITS-ATTR-MISSING" not in codes(path)


def test_a_declared_measurements_block_is_no_longer_refused(write_config, tmp_path):
    """The retirement. Over a table that really carries two rows per patient, so
    the honoured path is the one exercised — a config whose roster fails to
    resolve would pass this assertion without ever reaching the collapse."""
    (tmp_path / "input" / "index.csv").write_text(_MEASURED_CSV)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth", "read_id"],
                "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
            }
        }
    )
    found = codes(path)
    assert "E-DATA-MEASUREMENTS-UNSUPPORTED" not in found
    assert not [c for c in found if c.startswith("E-")], found


def test_a_typo_inside_the_measurements_block_is_now_reported(write_config, tmp_path):
    """The gap retiring the refusal would otherwise turn live. `measurements` is
    typed at `.by` and `.collapse` rather than left a whole leaf, so
    `check_envelope` descends into it and a misspelled child is a finding rather
    than a silently ignored key."""
    (tmp_path / "input" / "index.csv").write_text(_MEASURED_CSV)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth", "read_id"],
                "measurements": {"by": "read_id", "colapse": "mean"},
            }
        }
    )
    c = Collector()
    validate_config(path, c)
    unknown = [f for f in c.findings if f.code == "E-CONFIG-KEY-UNKNOWN"]
    assert unknown, {f.code for f in c.findings}
    assert unknown[0].path == "data.units.measurements.colapse"


def test_a_per_column_collapse_map_is_a_leaf_not_a_container(write_config, tmp_path):
    """`collapse: {depth: mean}` names COLUMNS, which no dotted path reaches. The
    closure must stop at `collapse` — descending would report every column name
    in the map as an unknown key, which is the trap a half-typed block sets."""
    (tmp_path / "input" / "index.csv").write_text(_MEASURED_CSV)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["depth", "read_id"],
                "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
            }
        }
    )
    assert "E-CONFIG-KEY-UNKNOWN" not in codes(path)


def test_a_non_mapping_measurements_block_is_still_typed(write_config):
    """Typing the children must not cost the block its own type check: the leaf
    entry stays in `LEAF_TYPES` beside them."""
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "measurements": "yes"}}
    )
    found = codes(path)
    # Both, not either: an `or` here would let an `E-CONFIG-TYPE` regression pass
    # on the strength of the finding this task did not add.
    assert "E-CONFIG-TYPE" in found
    assert "E-DATA-MEASUREMENTS-INVALID" in found


def test_check_measurements_called_directly_with_no_roster_still_finds_shape_faults():
    """The check must be exercisable on its own, not only reachable through
    `validate_config` — this is the direct-call route the brief asks for, and the
    one that proves the `roster is None` branch skips the type half without
    skipping the shape half."""
    c = Collector()
    _check_measurements({"measurements": {"collapse": "mean"}}, None, None, frozenset(), c)
    assert "E-DATA-MEASUREMENTS-INVALID" in {f.code for f in c.findings}
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" not in {f.code for f in c.findings}


def test_a_declared_contrast_is_no_longer_refused(write_config):
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman"]},
                },
                "statistics": {
                    "contrasts": [{"id": "s", "of": "method=spearman", "against": "baseline"}]
                },
            }
        )
    )
    assert "E-STATS-CONTRASTS-UNSUPPORTED" not in found
    # The positive claim, not just the absent refusal: `of`/`against` actually
    # resolved against real condition labels rather than merely failing to be
    # refused by the (now-retired) blanket code.
    assert "E-STATS-CONTRAST-UNKNOWN" not in found
    assert "E-STATS-CONTRAST-NESTED" not in found


def test_an_unresolvable_side_is_refused(write_config):
    assert "E-STATS-CONTRAST-UNKNOWN" in codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman"]},
                },
                "statistics": {
                    "contrasts": [{"id": "s", "of": "method=nope", "against": "baseline"}]
                },
            }
        )
    )


def test_a_contrast_naming_another_contrast_is_refused(write_config):
    """Contrasts do not nest — that is an interaction, and it belongs in a
    summary-step Estimate."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman"]},
                },
                "statistics": {
                    "contrasts": [
                        {"id": "a", "of": "method=spearman", "against": "baseline"},
                        {"id": "b", "of": "a", "against": "baseline"},
                    ]
                },
            }
        )
    )
    assert "E-STATS-CONTRAST-NESTED" in found


def test_no_declared_contrasts_still_validates_clean(write_config):
    found = codes(write_config({"statistics": {"contrasts": []}}))
    assert not [c for c in found if c.startswith("E-STATS-CONTRAST")]


def test_a_contrast_naming_an_unknown_within_attribute_is_refused(write_config):
    """The unknown-attribute case Task 2's review flagged: `within` naming a typo'd
    attribute would otherwise look exactly like a stratum that is genuinely empty,
    since `units_matching` reads it with `.get` either way."""
    found = codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["sex"]},
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman"]},
                },
                "statistics": {
                    "contrasts": [
                        {
                            "id": "s",
                            "of": "method=spearman",
                            "against": "baseline",
                            "within": {"sexx": "f"},
                        }
                    ]
                },
            }
        )
    )
    assert "E-STATS-CONTRAST-WITHIN" in found


def test_a_contrast_with_a_declared_within_attribute_validates_clean(write_config):
    found = codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["sex"]},
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman"]},
                },
                "statistics": {
                    "contrasts": [
                        {
                            "id": "s",
                            "of": "method=spearman",
                            "against": "baseline",
                            "within": {"sex": "f"},
                        }
                    ]
                },
            }
        )
    )
    assert "E-STATS-CONTRAST-WITHIN" not in found
    assert "E-STATS-CONTRAST-UNKNOWN" not in found


def test_a_declared_resample_is_refused(write_config):
    assert "E-STATS-RESAMPLE-UNSUPPORTED" in codes(
        write_config({"statistics": {"resample": {"method": "bootstrap", "n": 2000}}})
    )


def test_a_declared_null_test_is_refused(write_config):
    assert "E-STATS-NULLTEST-UNSUPPORTED" in codes(
        write_config({"statistics": {"null_test": {"method": "permutation", "n": 5000}}})
    )


def test_declared_report_by_is_checked_rather_than_refused(write_config):
    """S4d retires the blanket refusal and checks the declaration for real: with
    no `data.units.attributes` declared at all, `sex` is not among them, so this
    is now `E-STATS-REPORTBY-UNKNOWN` rather than the retired `-UNSUPPORTED`."""
    found = codes(write_config({"statistics": {"report_by": ["sex"]}}))
    assert "E-STATS-REPORTBY-UNSUPPORTED" not in found
    assert "E-STATS-REPORTBY-UNKNOWN" in found


def test_a_declared_hypothesis_is_checked_rather_than_refused(write_config):
    """S5b retires the blanket refusal and checks the declaration for real: `cli`
    now evaluates every declared hypothesis and writes its verdict, so a bare
    `metric: r` is `E-HYPOTHESIS-METRIC` — it names no step — rather than the
    retired `-UNSUPPORTED`."""
    found = codes(
        write_config({"hypotheses": [{"id": "h1", "metric": "r", "direction": "greater"}]})
    )
    assert "E-HYPOTHESIS-UNSUPPORTED" not in found
    assert "E-HYPOTHESIS-METRIC" in found


def test_empty_declarations_are_not_refused(write_config):
    """The generated config ships these keys empty; only a real declaration is
    refused, or every scaffolded project would fail to validate."""
    found = codes(
        write_config(
            {
                "statistics": {
                    "contrasts": [],
                    "resample": None,
                    "null_test": None,
                    "report_by": [],
                },
                "hypotheses": [],
            }
        )
    )
    assert not [c for c in found if "UNSUPPORTED" in c and ("STATS" in c or "HYPOTHESIS" in c)]


def test_correction_is_still_not_refused(write_config):
    found = codes(write_config({"statistics": {"correction": "holm"}}))
    assert not [c for c in found if c.startswith("E-STATS")]


def test_a_resolvable_roster_validates_clean(write_config, tmp_path):
    (tmp_path / "input" / "index.csv").write_text("patient_id,label\np1,0\np2,1\n")
    assert (
        codes(
            write_config(
                {
                    "data.units": {
                        "from": "index.csv",
                        "key": "patient_id",
                        "attributes": ["label"],
                    }
                }
            )
        )
        == set()
    )


def test_duplicate_keys_are_reported_as_a_diagnostic_not_an_exception(write_config, tmp_path):
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\np1\n")
    found = codes(write_config({"data.units": {"from": "index.csv", "key": "patient_id"}}))
    assert "E-UNITS-KEY-DUPLICATE" in found


def test_a_missing_key_column_is_reported_at_validate(write_config, tmp_path):
    (tmp_path / "input" / "index.csv").write_text("subject_id\ns1\n")
    assert "E-UNITS-KEY-MISSING" in codes(
        write_config({"data.units": {"from": "index.csv", "key": "patient_id"}})
    )


def test_a_reserved_attribute_name_is_reported_at_validate(write_config, tmp_path):
    (tmp_path / "input" / "index.csv").write_text("patient_id,paths\np1,x\n")
    assert "E-UNITS-ATTR-RESERVED" in codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "attributes": ["paths"],
                }
            }
        )
    )


def test_no_units_block_still_validates_clean(write_config):
    """`data.units` is optional; a pipeline with no unit table is legal."""
    assert codes(write_config()) == set()


def test_a_resolver_source_does_not_also_raise_source_missing(write_config):
    """`data.units.from.resolver` is already refused as `E-DATA-RESOLVER-UNSUPPORTED`;
    resolution must not also fire `E-UNITS-SOURCE-MISSING` for the same declaration —
    that would describe a resolver as a missing file rather than an unbuilt feature."""
    units = {"from": {"resolver": "plate_wells"}, "key": "well"}
    found = codes(write_config({"data.units": units}))
    assert "E-DATA-RESOLVER-UNSUPPORTED" in found
    assert "E-UNITS-SOURCE-MISSING" not in found


def test_an_unrelated_unsupported_field_does_not_suppress_a_real_roster_defect(
    write_config, tmp_path
):
    """`holdout` is refused, but it is not read by `resolve_units` at all — a
    duplicate key in the roster is a real, independent defect and must still be
    reported alongside the refusal, not swallowed by it."""
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\np1\n")
    units = {
        "from": "index.csv",
        "key": "patient_id",
        "holdout": {"method": "random", "frac": 0.2},
    }
    found = codes(write_config({"data.units": units}))
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
    assert "E-UNITS-KEY-DUPLICATE" in found


def test_a_string_units_block_is_reported_not_raised(write_config):
    """`data.units: "index.csv"` is an easy typo for the `from` key one level down —
    `validate_config` must return, with a diagnostic, not let an `AttributeError`
    escape. `_check_shape` catches this before any later check indexes into it, so
    the whole config is refused rather than partially validated."""
    path = _with_doc_change(write_config, lambda doc: doc["data"].update(units="index.csv"))
    c = Collector()
    result = validate_config(path, c)
    assert result is None
    assert "E-CONFIG-SHAPE" in {f.code for f in c.findings}


def test_a_list_units_block_is_reported_not_raised(write_config):
    path = _with_doc_change(write_config, lambda doc: doc["data"].update(units=["index.csv"]))
    c = Collector()
    result = validate_config(path, c)
    assert result is None
    assert "E-CONFIG-SHAPE" in {f.code for f in c.findings}


def test_a_malformed_units_block_is_reported_exactly_once(write_config):
    """`_check_shape` alone reports the bad `data.units` shape; `_check_units` and
    `_check_unimplemented` never even run because `validate_config` returns early —
    a bad shape must not produce the diagnostic twice."""
    path = _with_doc_change(write_config, lambda doc: doc["data"].update(units="index.csv"))
    c = Collector()
    validate_config(path, c)
    shape_findings = [f for f in c.findings if f.code == "E-CONFIG-SHAPE"]
    assert len(shape_findings) == 1


def test_check_unimplemented_alone_does_not_raise_on_a_malformed_units_block():
    """Exercised directly, the way `_check_unimplemented`'s other rules are —
    a non-mapping `data.units` reaching this function on its own (bypassing
    `_check_shape`, which normally would have stopped `validate_config` first) must
    still produce a diagnostic rather than an `AttributeError`."""
    from publishable.validate import _check_unimplemented

    c = Collector()
    _check_unimplemented({"data": {"units": "index.csv"}}, c)
    assert "E-CONFIG-SHAPE" in {f.code for f in c.findings}


@pytest.mark.parametrize(
    "block,bad_value",
    [
        ("metadata", "not-a-mapping"),
        ("metadata", ["a", "list"]),
        ("data", "not-a-mapping"),
        ("data", ["a", "list"]),
        ("parameters", "not-a-mapping"),
        ("parameters", ["a", "list"]),
        ("sweep", "not-a-mapping"),
        ("sweep", ["a", "list"]),
        ("replication", "not-a-mapping"),
        ("replication", ["a", "list"]),
        ("statistics", "not-a-mapping"),
        ("statistics", ["a", "list"]),
        ("limits", "not-a-mapping"),
        ("limits", ["a", "list"]),
        ("hypotheses", "not-a-list"),
        ("hypotheses", {"a": "mapping"}),
        ("schema_version", ["a", "list"]),
        ("schema_version", {"a": "mapping"}),
        ("experiment_type", ["a", "list"]),
        ("template_version", ["a", "list"]),
        ("entrypoint", ["a", "list"]),
        ("plugin", ["a", "list"]),
    ],
)
def test_a_top_level_block_with_the_wrong_shape_is_reported_not_raised(
    write_config, block, bad_value
):
    """Every block `_check_shape` guards, exercised with a string where a mapping/list
    is expected and a list where a string/mapping is expected — the same crash class
    the review found in `data.units`, one level up. `validate_config` must return
    `None` rather than let the type error escape into a later `_check_*`."""
    path = _with_doc_change(write_config, lambda doc: doc.update({block: bad_value}))
    c = Collector()
    result = validate_config(path, c)
    assert result is None
    assert "E-CONFIG-SHAPE" in {f.code for f in c.findings}


def test_a_repeats_item_that_is_not_a_mapping_is_reported_not_raised(write_config):
    """`replication.repeats: [1, 2]` crashed `_check_replication`'s `level.get("n")`
    before this guard existed."""
    path = _with_doc_change(write_config, lambda doc: doc["replication"].update(repeats=[1, 2]))
    c = Collector()
    result = validate_config(path, c)
    assert result is None
    assert "E-CONFIG-SHAPE" in {f.code for f in c.findings}


@pytest.mark.parametrize(
    "bad_repeats",
    [
        {"kind": "seed", "n": 5},  # the forgotten `-` on `repeats`: a mapping, not a list
        "seed",
        5,
    ],
)
def test_a_repeats_block_that_is_not_a_list_is_reported_not_raised(write_config, bad_repeats):
    """`_check_shape` guarded the ITEMS of `replication.repeats` but not the container
    itself — when `repeats` is a mapping, a string, or a number, the per-item loop is
    simply skipped, no finding fires, and `_check_replication` then crashes on
    `level.get("n")`. This is the single most plausible YAML mistake in this file: a
    user writes `repeats:` followed by an indented mapping, forgetting the `-` that
    would make it a list item."""
    path = _with_doc_change(
        write_config, lambda doc: doc["replication"].update(repeats=bad_repeats)
    )
    c = Collector()
    result = validate_config(path, c)
    assert result is None
    assert "E-CONFIG-SHAPE" in {f.code for f in c.findings}


def test_a_correctly_shaped_repeats_list_still_validates_clean(write_config_nondet):
    """The new container check must not become a false refusal against a `repeats`
    that is legitimately a list of mappings. `fold` is a genuine refusal now that
    `_check_replication` calls `resolve_repeats`, so this uses two supported kinds —
    and a `batch` needs a nondeterministic step, or `W-REPL-DETERMINISTIC` fires."""
    path = _with_doc_change(
        write_config_nondet,
        lambda doc: doc["replication"].update(
            repeats=[{"kind": "batch", "n": 2}, {"kind": "seed", "n": 5}]
        ),
    )
    assert codes(path) == set()


def test_a_non_list_attributes_block_is_reported_not_raised(write_config, tmp_path):
    """`data.units.attributes` is iterated and indexed by `resolve_units` — a
    non-iterable scalar (e.g. an int) raises a bare `TypeError` there, which
    `_check_units`'s `except ContractError` does not catch. Caught here instead,
    before resolution ever runs."""
    (tmp_path / "input" / "index.csv").write_text("patient_id,label\np1,0\n")
    path = _with_doc_change(
        write_config,
        lambda doc: doc["data"].update(
            units={"from": "index.csv", "key": "patient_id", "attributes": 5}
        ),
    )
    c = Collector()
    result = validate_config(path, c)
    assert result is None
    assert "E-CONFIG-SHAPE" in {f.code for f in c.findings}


def test_a_fully_valid_config_still_validates_completely_clean(write_config):
    """The new shape gate must not become a false refusal against the config every
    other test in this file already treats as valid."""
    assert codes(write_config()) == set()


def test_an_absent_optional_block_is_not_a_shape_error(write_config):
    """`sweep` and `statistics` are optional and absent in the base fixture; absence
    must not be confused with the wrong shape."""
    path = write_config()
    loaded = yaml.safe_load(path.read_text())
    assert "sweep" not in loaded
    assert "statistics" not in loaded
    assert codes(path) == set()


def test_a_missing_entrypoint_is_reported(write_config):
    """A config `validate` blesses must be one `run` can actually execute — deleting
    `entrypoint` used to pass validation and then die inside `run` with a bare
    `KeyError`."""
    assert "E-ENTRYPOINT-REQUIRED" in codes(write_config({"entrypoint": _DELETE}))


def test_an_empty_entrypoint_is_reported(write_config):
    assert "E-ENTRYPOINT-REQUIRED" in codes(write_config({"entrypoint": ""}))


def test_a_missing_input_manifest_policy_is_reported(write_config):
    """Same gap, different field: deleting `data.input_manifest_policy` used to pass
    validation and then die inside `run` with a bare `KeyError`."""
    assert "E-DATA-POLICY" in codes(write_config({"data.input_manifest_policy": _DELETE}))


def test_an_unknown_input_manifest_policy_is_reported(write_config):
    """Setting it to a value outside `manifest.POLICIES` used to reach `manifest.py`
    and raise a bare `ValueError` that `main` does not catch."""
    assert "E-DATA-POLICY" in codes(write_config({"data.input_manifest_policy": "bogus"}))


def test_a_template_cross_field_rule_is_reported(write_config, monkeypatch):
    """`generic` has no cross-field rule of its own, so `E-TEMPLATE-RULE` is exercised
    through a stub template swapped in for the registry lookup `validate_config` makes."""
    import publishable.validate as validate_mod
    from publishable.templates.builtin.generic import GenericTemplate

    class RuleBreaker(GenericTemplate):
        def validate(self, config):
            return ["a cross-field rule was broken"]

    monkeypatch.setattr(validate_mod, "get_template", lambda name: RuleBreaker())
    assert "E-TEMPLATE-RULE" in codes(write_config())


def test_falling_below_the_repeat_floor_warns():
    """Exercised directly: `generic`'s floor is 1, so no legal count can breach it.

    Routing this through `validate_config` would need a template that does not
    exist yet, and asserting the warning against an illegal `n: 0` would be
    testing the error path while claiming to test the floor.
    """
    from publishable.templates.base import BaseTemplate
    from publishable.validate import _check_replication

    class Benchmark(BaseTemplate):
        default_repeats = 5

    c = Collector()
    _check_replication({"replication": {"repeats": [{"kind": "seed", "n": 3}]}}, Benchmark(), c)
    findings = [f for f in c.findings if f.code == "W-REPL-FLOOR"]
    assert len(findings) == 1
    assert "3" in findings[0].message and "5" in findings[0].message

    clean = Collector()
    _check_replication({"replication": {"repeats": [{"kind": "seed", "n": 5}]}}, Benchmark(), clean)
    assert clean.findings == []


# --- `sweep.baseline` is validated, shaped, and refused when partial -------------


def test_a_baseline_path_must_be_a_real_parameter(write_config):
    """`reference.md`:218, "Baseline is a valid condition". Unchecked, a misspelled
    baseline path was planted verbatim into condition `00`'s config and the run
    reported success having executed the base config under a baseline label."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.methd": "pearson"},
                    "grid": {"analysis.methd": ["spearman", "kendall"]},
                }
            }
        )
    )
    assert "E-SWEEP-PATH-UNKNOWN" in found


def test_a_baseline_value_must_satisfy_its_param(write_config):
    """`reference.md`:218's own example: `sweep.baseline` sets `analysis.method:
    pearsonn`. Before this check the config validated with only `W-STATS-FAMILY`."""
    found = messages_by_code(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearsonn"},
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                }
            }
        )
    )
    assert "E-PARAM-VALUE" in found


def test_a_baseline_value_is_not_subject_to_the_nameability_check(write_config):
    """A baseline condition's label is the literal `baseline` (`sweep.label_for`),
    so a baseline's fixed values are never rendered into a label. Refusing an
    unnameable one would reject a legal config — and stays legal under the per-cell
    expansion, which labels a baseline by the axes it leaves free.

    The value has to be one `check_swept_value` actually refuses, or the test
    passes under either setting of `_value_checks`'s `nameable`. `pear son` fails
    `SWEPT_VALUE_PATTERN` on the space. Both directions are
    asserted on the one config: the `Param` check *is* applied to a baseline entry
    (`reference.md`:218), the nameability check is not."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pear son"},
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                }
            }
        )
    )
    assert "E-PARAM-VALUE" in found
    assert "E-SWEEP-VALUE-UNNAMEABLE" not in found


def test_a_baseline_that_leaves_a_grid_axis_free_validates_and_expands(write_config):
    """§ Expansion modes' second row — the one the section tells a reader to prefer
    — is a config core accepts, and it executes the design it declares.

    `E-SWEEP-BASELINE-PARTIAL` refused exactly this shape while `expand` emitted a
    single `00_baseline`. Both halves are asserted on the one config, because a
    clean `validate` over a wrong expansion is what the retired refusal existed to
    prevent: the baseline fixes `analysis.method` and leaves `analysis.min_samples`
    free, so it expands to one baseline per level of the free axis, ahead of the
    2 × 2 product."""
    path = write_config(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {
                    "analysis.method": ["spearman", "kendall"],
                    "analysis.min_samples": [10, 20],
                },
            }
        }
    )
    assert codes(path) == set()

    conditions = expand(yaml.safe_load(path.read_text()))
    assert [c.label for c in conditions] == [
        "min_samples=10__baseline",
        "min_samples=20__baseline",
        "method=spearman__min_samples=10",
        "method=spearman__min_samples=20",
        "method=kendall__min_samples=10",
        "method=kendall__min_samples=20",
    ]
    assert [c.is_baseline for c in conditions] == [True, True, False, False, False, False]
    # Each baseline carries the axis it fixes *and* its own cell — the point of
    # the expansion, and what a single `00_baseline` could not say.
    assert dict(conditions[0].values) == {
        "analysis.method": "pearson",
        "analysis.min_samples": 10,
    }


def test_a_baseline_that_leaves_a_paired_axis_free_validates_and_expands(write_config):
    """The same shape one mode over: a `paired` axis sets several paths per cell, so
    the baseline that leaves it free expands over its *cells* rather than over a
    list of values, and each baseline row carries both of the cell's paths."""
    path = write_config(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall"]},
                "paired": [
                    {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                    {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                ],
            }
        }
    )
    assert codes(path) == set()

    conditions = expand(yaml.safe_load(path.read_text()))
    assert [c.is_baseline for c in conditions] == [True, True, False, False, False, False]
    assert dict(conditions[1].values) == {
        "analysis.method": "pearson",
        "analysis.min_samples": 50,
        "analysis.confidence": 0.99,
    }


def test_a_baseline_fixing_every_axis_including_paired_is_one_condition(write_config):
    """The other row of the same table: a baseline naming every path any axis-shaped
    mode sweeps — `grid`'s and `paired`'s alike — has nothing to expand over and is
    condition `00` alone."""
    path = write_config(
        {
            "sweep": {
                "baseline": {
                    "analysis.method": "pearson",
                    "analysis.min_samples": 30,
                    "analysis.confidence": 0.95,
                },
                "grid": {"analysis.method": ["spearman", "kendall"]},
                "paired": [
                    {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                    {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                ],
            }
        }
    )
    assert codes(path) == set()

    conditions = expand(yaml.safe_load(path.read_text()))
    assert [c.label for c in conditions][0] == "baseline"
    assert [c.is_baseline for c in conditions] == [True, False, False, False, False]


def test_a_baseline_fixing_every_axis_is_one_condition(write_config):
    """The row the slice's worked example uses, and it must keep working."""
    path = write_config(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
                "grid": {"analysis.min_samples": [10, 20]},
            }
        }
    )
    assert codes(path) == set()
    assert [c.is_baseline for c in expand(yaml.safe_load(path.read_text()))] == [
        True,
        False,
        False,
    ]


def test_a_bare_baseline_with_no_grid_is_one_condition(write_config):
    """No axis means nothing to expand over, so the bare-baseline level stays what
    it was: one condition, labelled `baseline`."""
    path = write_config({"sweep": {"baseline": {"analysis.method": "pearson"}}})
    assert codes(path) == set()
    conditions = expand(yaml.safe_load(path.read_text()))
    assert [(c.label, c.is_baseline) for c in conditions] == [("baseline", True)]


def test_an_empty_baseline_beside_a_grid_yields_no_baseline_condition(write_config):
    """`baseline: {}` declares nothing; "present but empty is not a declaration" is
    this repo's convention elsewhere too. It is *not* read as a baseline fixing no
    swept path and expanded over every axis — that would double a grid whose author
    declared no reference at all."""
    path = write_config(
        {"sweep": {"baseline": {}, "grid": {"analysis.method": ["spearman", "kendall"]}}}
    )
    assert codes(path) == set()
    conditions = expand(yaml.safe_load(path.read_text()))
    assert [(c.label, c.is_baseline) for c in conditions] == [
        ("method=spearman", False),
        ("method=kendall", False),
    ]


def test_a_list_grid_is_a_diagnostic_not_a_traceback(write_config):
    """`_check_sweep` calls `grid.items()`; without the shape guard this escaped
    `main`'s handler as `AttributeError: 'list' object has no attribute 'items'`."""
    found = codes(write_config({"sweep": {"grid": ["analysis.method"]}}))
    assert "E-CONFIG-SHAPE" in found


def test_a_grid_with_a_non_string_int_key_is_a_diagnostic_not_a_traceback(write_config):
    """Same class as `paired`'s non-string-key guard, reached through `grid`
    instead: YAML permits `123: [...]` as a mapping key, but `_keys_for` feeds
    every swept path into `.split(".")`, so this crashed
    `AttributeError: 'int' object has no attribute 'split'` before this guard
    existed. Pre-existing and independent of the `paired` finding — found by
    the same review pattern applied to `grid`."""
    found = codes(write_config({"sweep": {"grid": {123: ["a", "b"]}}}))
    assert "E-CONFIG-SHAPE" in found


def test_a_grid_with_a_non_string_float_key_is_a_diagnostic_not_a_traceback(write_config):
    """Same crash, via a `float` key instead of `int`."""
    found = codes(write_config({"sweep": {"grid": {1.5: ["a", "b"]}}}))
    assert "E-CONFIG-SHAPE" in found


def test_a_list_baseline_is_a_diagnostic_not_a_traceback(write_config):
    """`sweep.expand` calls `dict(baseline)`; without the guard this escaped as
    `ValueError: dictionary update sequence element #0 has length 15`."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": ["analysis.method"],
                    "grid": {"analysis.method": ["spearman"]},
                }
            }
        )
    )
    assert "E-CONFIG-SHAPE" in found


def test_a_bare_string_axis_is_refused_rather_than_expanded_per_character(write_config):
    """Forgotten brackets: `grid: {analysis.method: spearman}` is iterable, so it
    expanded into one condition per letter. A template with an unconstrained `str`
    parameter would have taken that expansion clean."""
    path = write_config({"sweep": {"grid": {"analysis.method": "spearman"}}})
    c = Collector()
    validate_config(path, c)
    shape = [f for f in c.findings if f.code == "E-CONFIG-SHAPE"]
    assert [f.path for f in shape] == ["sweep.grid.analysis.method"]
    assert "expected a list" in shape[0].message


def test_a_null_grid_or_baseline_is_absent_not_malformed(write_config):
    """A key present but `null` is treated as absent everywhere else in this
    module (`doc.get("x") or {}`), and the shape guard must not diverge."""
    found = codes(write_config({"sweep": {"baseline": None, "grid": None}}))
    assert "E-CONFIG-SHAPE" not in found


def test_a_non_list_paired_is_a_diagnostic_not_a_traceback(write_config):
    """`_axes` now reads `paired` unconditionally (`dict(entry) for entry in
    paired`), same as `grid`'s unguarded `.items()` before ad6cf3d — so a
    non-list `paired` needs the identical container guard `grid` already has,
    or it crashes `expand` inside `cli.run` rather than `validate`."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.method": ["spearman"]},
                    "paired": "analysis.min_samples",
                }
            }
        )
    )
    assert "E-CONFIG-SHAPE" in found


def test_a_paired_entry_that_is_not_a_mapping_is_a_diagnostic_not_a_traceback(write_config):
    """`dict(entry)` inside `_axes`'s paired branch raises `ValueError` on a
    non-mapping entry — `["notadict"]` reproduces exactly the crash the
    reviewer found: zero `validate` findings, then a bare `ValueError:
    dictionary update sequence element #0 has length 1; 2 is required` out of
    `cli.py`'s `expand(doc)`, past `main`'s `PublishableError` handler."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                    "paired": ["notadict"],
                }
            }
        )
    )
    assert "E-CONFIG-SHAPE" in found


def test_a_null_paired_entry_is_a_diagnostic_not_a_traceback(write_config):
    """`sweep`-level `null` (`sweep.paired: null`) is absent, matching the rest
    of this module — but a `null` *entry inside* an otherwise-list `paired` is
    not the same case: `_axes` feeds every entry straight to `dict()`, and
    `dict(None)` raises `TypeError` exactly like `dict(["notadict"][0])` raises
    `ValueError` above. A `grid` axis value stays legal as `null` because it is
    used as-is (a param-value question); a `paired` entry has no such out."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                    "paired": [None],
                }
            }
        )
    )
    assert "E-CONFIG-SHAPE" in found


def test_a_null_whole_paired_block_is_absent_not_malformed(write_config):
    """`sweep.paired: null` is the block-level case the rest of this module
    treats as absent (`doc.get("x") or {}`), distinct from a `null` entry
    inside a present list, which the test above refuses."""
    found = codes(
        write_config(
            {"sweep": {"grid": {"analysis.method": ["spearman", "kendall"]}, "paired": None}}
        )
    )
    assert "E-CONFIG-SHAPE" not in found


def test_a_paired_entry_with_a_non_string_int_key_is_a_diagnostic_not_a_traceback(write_config):
    """`dict()` tolerates a non-string key (`{123: 30}` parses fine off YAML), but
    `_swept_paths`/`_keys_for` feed every `paired` key into `.split(".")` and an
    `endswith` scan, both string-only — `123.split(".")` is
    `AttributeError: 'int' object has no attribute 'endswith'` (actually raised
    inside `_keys_for`'s `path.split(".")` first) once `expand` reaches
    `label_for`. Reproduced directly against `expand` before this guard existed:
    `AttributeError: 'int' object has no attribute 'endswith'`."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.method": ["pearson", "spearman"]},
                    "paired": [{123: 30}, {123: 50}],
                }
            }
        )
    )
    assert "E-CONFIG-SHAPE" in found


def test_a_paired_entry_with_a_non_string_float_key_is_a_diagnostic_not_a_traceback(write_config):
    """Same crash, via a `float` key instead of `int` — confirms the guard checks
    `isinstance(key, str)` rather than special-casing one non-string type."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "grid": {"analysis.method": ["pearson", "spearman"]},
                    "paired": [{1.5: 30}, {1.5: 50}],
                }
            }
        )
    )
    assert "E-CONFIG-SHAPE" in found


def test_check_contrasts_still_refuses_a_non_list_when_called_directly():
    """`_check_contrasts`'s own `isinstance(entries, list)` guard is kept even
    though `_check_shape` now refuses that shape first in the normal pipeline
    (`validate_config` early-returns before `_check_contrasts` ever runs for a
    non-list block). The guard is still live for a caller that reaches
    `_check_contrasts` directly, which is exactly why it was kept rather than
    deleted as newly redundant."""
    c = Collector()
    _check_contrasts({"statistics": {"contrasts": {"id": "x"}}}, c)
    assert "E-STATS-CONTRAST-SHAPE" in {f.code for f in c.findings}


def test_check_contrasts_guards_expand_when_called_directly():
    """`_check_contrasts` calls `expand(doc)` unguarded to resolve condition
    labels for `of`/`against` — a `null` `sweep.grid` axis value reaches it
    (`_check_shape`'s per-axis `list` guard refuses only a *present, non-list*
    value, not `null`) and `itertools.product` raises `TypeError` on a `None`
    iterable. `_check_sweep` calls the same pure `expand(doc)` on the same doc
    one line earlier in the normal `validate_config` pipeline and is now
    guarded too (`test_a_malformed_sweep_with_contrasts_is_a_diagnostic_not_a_crash`
    exercises that end to end), so this direct call is what proves the guard
    inside `_check_contrasts` is live in its own right — the same reason
    `test_check_contrasts_still_refuses_a_non_list_when_called_directly`'s own
    shape guard was kept rather than deleted as redundant once `_check_shape`
    also covers it."""
    c = Collector()
    _check_contrasts(
        {
            "sweep": {"grid": {"analysis.method": None}},
            "statistics": {"contrasts": [{"id": "x", "of": "a", "against": "b"}]},
        },
        c,
    )
    # `conditions = []` on the guarded `expand`, not a bare early `return`: the
    # shape checks still run and both sides resolve against an empty `labels`,
    # so each is reported unknown rather than the whole block going unchecked.
    codes_found = [f.code for f in c.findings]
    assert codes_found.count("E-STATS-CONTRAST-UNKNOWN") == 2


def test_a_malformed_sweep_with_contrasts_is_a_diagnostic_not_a_crash(write_config):
    """The acceptance test Debt B's brief actually specified: a config whose
    `sweep` cannot expand *and* whose `statistics.contrasts` is declared,
    through `validate_config` end to end. Before the fix this raised
    `TypeError: 'NoneType' object is not iterable` out of `_check_sweep`'s own
    unguarded `expand(doc)` call — one statement before `_check_contrasts`
    ever runs — so guarding `_check_contrasts` alone did not make this
    pass."""
    path = write_config(
        {
            "sweep": {"grid": {"analysis.method": None}},
            "statistics": {"contrasts": [{"id": "x", "of": "a", "against": "b"}]},
        }
    )
    c = Collector()
    validate_config(path, c)  # must not raise
    assert c.findings  # a diagnostic, not silence


def test_a_malformed_sweep_alone_with_no_contrasts_is_also_a_diagnostic(write_config):
    """The crash this task found does not need `statistics.contrasts` at all
    — `_check_sweep`'s own `expand(doc)` call is what raises, and it runs
    whether or not any contrast is declared. Kept as a separate case from the
    one above so a future fix scoped only to `_check_contrasts` (which would
    leave this one failing) is caught."""
    path = write_config({"sweep": {"grid": {"analysis.method": None}}})
    c = Collector()
    validate_config(path, c)  # must not raise
    assert c.findings


def test_a_scalar_contrasts_block_is_refused_once_in_the_shape_pass(write_config):
    """`_check_shape` runs first and `validate_config` early-returns on it, so a
    nested key refused there is refused for every later reader at once. Its own
    comment says an unguarded container means "the crash just moves one level
    down, into whichever `_check_*` reads it next" — which is what R11 was."""
    found = codes(write_config({"statistics": {"contrasts": 5}}))
    assert "E-CONFIG-SHAPE" in found


# --- `validate` loads the experiment, so it can answer W-REPL-DETERMINISTIC -----


def test_a_batch_level_warns_when_no_step_is_nondeterministic(write_config):
    assert "W-REPL-DETERMINISTIC" in codes(
        write_config({"replication": {"repeats": [{"kind": "batch", "n": 3}]}})
    )


def test_no_warning_when_a_step_declares_nondeterminism(write_config_nondet):
    assert "W-REPL-DETERMINISTIC" not in codes(
        write_config_nondet({"replication": {"repeats": [{"kind": "batch", "n": 3}]}})
    )


def test_no_warning_without_a_batch_level(write_config):
    assert "W-REPL-DETERMINISTIC" not in codes(
        write_config({"replication": {"repeats": [{"kind": "seed", "n": 3}]}})
    )


def test_an_unimportable_entrypoint_is_a_finding_not_a_traceback(write_config_broken):
    """validate collects; a broken step module must not escape as a traceback."""
    found = codes(write_config_broken({}))
    assert "E-ENTRYPOINT-IMPORT" in found


def test_a_broken_entrypoint_does_not_also_warn_about_determinism(write_config_broken):
    """One finding per fault. A pipeline nobody could load has no steps to read
    `nondeterministic` off, so a second warning about its `batch` is noise."""
    found = codes(write_config_broken({"replication": {"repeats": [{"kind": "batch", "n": 3}]}}))
    assert "E-ENTRYPOINT-IMPORT" in found
    assert "W-REPL-DETERMINISTIC" not in found


def test_the_import_failure_message_names_the_exception(write_config_broken):
    message = messages_by_code(write_config_broken({}))["E-ENTRYPOINT-IMPORT"]
    assert "RuntimeError" in message and "module scope blew up" in message


def test_an_entrypoint_that_exits_at_module_scope_is_reported_not_propagated(
    write_config_exits,
):
    """`sys.exit()` at import is a SystemExit, which is not an Exception.

    Without an explicit arm it escapes `validate`'s catch and takes the process
    with it — the user's exit code, and no diagnostic naming the entrypoint.
    """
    message = messages_by_code(write_config_exits({}))["E-ENTRYPOINT-IMPORT"]
    assert "SystemExit" in message


def test_an_entrypoint_without_a_colon_says_so_rather_than_blaming_the_import(write_config):
    """`load_experiment` refuses a value that is not `<module>:<attribute>` before it
    imports anything. That branch was only reachable through `run` until `validate`
    began loading the entrypoint, and "could not be imported" would send the reader
    looking for a missing module instead of a malformed config line."""
    message = messages_by_code(write_config({"entrypoint": "cohort_pilot.experiment"}))[
        "E-ENTRYPOINT-IMPORT"
    ]
    assert "is not `<module>:<attribute>`" in message
    assert "could not be imported" not in message


_TWO_CONDITIONS = {
    "baseline": {"analysis.method": "pearson"},
    "grid": {"analysis.method": ["spearman"]},
}


def test_a_contrast_comparing_a_condition_with_itself_is_refused(write_config):
    """`reference.md` § Validation, "Contrast has two distinct sides". Left
    unchecked it publishes a perfect null with a zero-width interval over every
    unit as a finding, and takes a slot in the correction family while doing
    it."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {
                    "contrasts": [{"id": "selfie", "of": "baseline", "against": "baseline"}]
                },
            }
        )
    )
    assert "E-STATS-CONTRAST-SAME-SIDES" in found


def test_a_contrast_with_an_unresolvable_side_is_unknown_not_same_sides(write_config):
    """Both sides identical *and* neither resolving is a typo, not a
    self-comparison; the more specific diagnostic has to win, or a misspelled
    label reads as a design mistake the author didn't make."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {"contrasts": [{"id": "x", "of": "nosuch", "against": "nosuch"}]},
            }
        )
    )
    assert "E-STATS-CONTRAST-UNKNOWN" in found
    assert "E-STATS-CONTRAST-SAME-SIDES" not in found


def test_an_unhashable_side_inside_a_well_shaped_contrast_is_refused_not_a_crash(write_config):
    """`of`/`against` naming a list rather than a condition label: `_check_shape`
    accepts this (`statistics.contrasts` is a list of mappings, so the container
    shape is fine), and before this fix `_check_contrasts` raised `TypeError:
    unhashable type: 'list'` from `value in ids` — a set membership test with no
    `isinstance` guard, unlike the `E-STATS-CORRECTION-UNKNOWN` check ~130 lines
    above that does guard it. `validate.py` collects findings and never raises,
    so this has to come back as a diagnostic through `validate_config` end to
    end, not merely from a function called directly."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {"contrasts": [{"id": "x", "of": ["a", "b"], "against": "baseline"}]},
            }
        )
    )
    assert "E-STATS-CONTRAST-UNKNOWN" in found


@pytest.mark.parametrize("bad_id", [{"name": "sensitivity"}, ["sensitivity"]])
def test_an_unhashable_contrast_id_is_refused_not_a_crash(write_config, bad_id):
    """The sibling of the `of`/`against` fix above, at the two sites that read
    `id`: the `ids` **set construction** that collects every entry's `id` before
    the loop, and the `in seen_ids` repeat check inside it. Both hash whatever
    `id` holds, so a mapping (one bad indent under `id:`) or a list raised
    `TypeError: unhashable type` out of `validate_config` before any finding was
    collected — and because `run` validates first, `run` got the traceback too.
    `validate.py` collects findings and never raises, so a non-string `id` has
    to come back as the diagnostic the missing/non-string branch already gives
    it, through `validate_config` end to end."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {
                    "contrasts": [{"id": bad_id, "of": "method=spearman", "against": "baseline"}]
                },
            }
        )
    )
    assert "E-STATS-CONTRAST-SHAPE" in found


def test_a_contrast_entry_that_is_not_a_mapping_is_refused(write_config):
    """A list of condition labels where a list of contrast entries belongs.
    `resolve_contrasts` reads `entry["of"]` off whatever this holds, so before
    this check the slip reached `run` as an `AttributeError` traceback — and
    `contrasts.py`'s own comment leans on validate having refused it."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {"contrasts": ["method=spearman"]},
            }
        )
    )
    assert "E-STATS-CONTRAST-SHAPE" in found


def test_a_non_list_contrasts_block_is_refused(write_config):
    """A mapping where `statistics.contrasts` wants a list: refused in `_check_shape`
    now, upstream of `_check_contrasts`, so this is `E-CONFIG-SHAPE` rather than
    `E-STATS-CONTRAST-SHAPE` — `validate_config` early-returns on the shape pass
    before `_check_contrasts` ever runs."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {"contrasts": {"id": "x", "of": "baseline"}},
            }
        )
    )
    assert "E-CONFIG-SHAPE" in found


def test_a_contrast_without_an_id_is_refused(write_config):
    """`id` names the entry in `results.contrasts` and in a hypothesis. Missing,
    it reached the record as the literal string `'None'`, and two such entries
    collided under one name."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {"contrasts": [{"of": "method=spearman", "against": "baseline"}]},
            }
        )
    )
    assert "E-STATS-CONTRAST-SHAPE" in found


def test_two_contrasts_cannot_share_one_id(write_config):
    """`id` is how an entry is named in `results.contrasts` and in a hypothesis,
    so two under one name are indistinguishable in both — which is what the
    missing-`id` diagnostic already tells the author."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {
                    "contrasts": [
                        {"id": "same", "of": "method=spearman", "against": "baseline"},
                        {"id": "same", "of": "baseline", "against": "method=spearman"},
                    ]
                },
            }
        )
    )
    assert "E-STATS-CONTRAST-SHAPE" in found


def test_declared_contrasts_are_counted_in_the_uncorrected_family(write_config):
    """`reference.md` § Contrasts: "Declared contrasts join the correction family
    alongside baseline comparisons, because a reader shown both is exposed to
    both." Counting only `len(conditions) - 1` was accurate while the block was
    refused wholesale and is not any more — a two-condition run with two
    declared contrasts publishes three comparisons per metric, not one."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {
                    "correction": "none",
                    "contrasts": [
                        {"id": "a", "of": "method=spearman", "against": "baseline"},
                        {"id": "b", "of": "baseline", "against": "method=spearman"},
                    ],
                },
            }
        ),
        c,
    )
    warning = next(f for f in c.findings if f.code == "W-STATS-FAMILY")
    assert "3 comparisons" in warning.message


def test_a_scalar_contrasts_block_is_refused_without_raising(write_config):
    """A *scalar* where a list belongs, not a mapping: `len()` works on a mapping
    and raises on a bool or an int, and the family count in `_check_sweep` used to
    read the block before `_check_contrasts` refused its shape. `_check_shape` now
    refuses any non-list `statistics.contrasts` upstream of both, so this comes
    back as `E-CONFIG-SHAPE` — the assertion is still that `validate_config`
    returns a diagnostic rather than raising."""
    for block in (5, True, "method=spearman"):
        found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"contrasts": block}}))
        assert "E-CONFIG-SHAPE" in found


def test_the_default_correction_does_not_warn_about_the_family(write_config):
    """`materialize.py` writes `correction: holm` into every generated config, so
    a warning on the default is a warning nearly every run gets. It fires for
    `none` — `reference.md` § Validation: "Correction declared for a family ...
    with `statistics.correction: none` (warning)"."""
    found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "holm"}}))
    assert "W-STATS-FAMILY" not in found


def test_an_uncorrected_family_still_warns(write_config):
    found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "none"}}))
    assert "W-STATS-FAMILY" in found


def test_a_sweep_with_no_baseline_and_no_contrasts_has_no_family(write_config):
    """The overcount recorded in `spec-defects.md`: a grid-only sweep declares no
    baseline, so `resolve_contrasts` returns `[]` and the run publishes no
    comparison at all. Counting `len(conditions) - 1` told the author they had a
    family of two."""
    found = codes(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
                "statistics": {"correction": "none"},
            }
        )
    )
    assert "W-STATS-FAMILY" not in found


def test_fdr_bh_over_a_family_with_no_p_value_warns(write_config):
    """`reference.md`: `fdr_bh` "needs a p-value it can't always get. Declared
    over a family whose metrics carry none, it leaves every member with a `null`
    `ci95_corrected` and no `p_value_corrected` either — a correction declared
    and not applied, which is the state this section exists to prevent." No
    comparison in this build can carry one: `statistics.null_test` is refused."""
    found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "fdr_bh"}}))
    assert "W-STATS-CORRECTION-INAPPLICABLE" in found


def test_holm_over_the_same_family_does_not_warn_about_applicability(write_config):
    """Holm's correction is interval-shaped, so it applies without a p-value.
    A warning here would read as "no correction is possible", which is false."""
    found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "holm"}}))
    assert "W-STATS-CORRECTION-INAPPLICABLE" not in found


def test_a_non_string_correction_is_refused_without_raising(write_config):
    """`validate.py` collects findings and never raises — including on a config
    value of the wrong type. The family block reads `correction` before anything
    checks its shape, which is the class of the R11 regression in S4b."""
    for value in (5, True, ["holm"], {"method": "holm"}):
        found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": value}}))
        assert "E-STATS-CORRECTION-UNKNOWN" in found


def test_an_out_of_enum_correction_string_is_refused(write_config):
    """`bonferonni` is a plausible typo of `bonferroni`. Left unchecked it
    collects zero findings, and `corrected_for` downstream returns
    `ci95_corrected: null`, `correction: "bonferonni"`, `correction_level: null`,
    `thin: false` — a correction recorded as applied while none was, and `thin:
    false` suppresses the one signal that would otherwise flag it. `reference.md`
    § The one config file enumerates `none | bonferroni | holm | fdr_bh` and
    nothing else is a legal value."""
    found = codes(
        write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "bonferonni"}})
    )
    assert "E-STATS-CORRECTION-UNKNOWN" in found


_UNITS_WITH_SEX = {"from": "index.csv", "key": "patient_id", "attributes": ["sex"]}


def test_a_declared_report_by_is_no_longer_refused(write_config):
    """S4d implements it, so the blanket refusal retires with the slice — the
    same way `E-STATS-CONTRASTS-UNSUPPORTED` retired with S4b."""
    found = codes(
        write_config({"data.units": _UNITS_WITH_SEX, "statistics": {"report_by": ["sex"]}})
    )
    assert "E-STATS-REPORTBY-UNSUPPORTED" not in found
    assert "E-STATS-REPORTBY-UNKNOWN" not in found


def test_a_report_by_attribute_must_be_declared(write_config):
    """`reference.md` § Reporting strata: "validate rejects a `report_by`
    attribute that isn't declared in `data.units.attributes`". Left unchecked,
    `strata.levels_for` returns `{}` for a typo, which is indistinguishable from
    an attribute no unit happens to carry — the record would simply hold no `by`
    block and never say why."""
    found = codes(
        write_config({"data.units": _UNITS_WITH_SEX, "statistics": {"report_by": ["sexx"]}})
    )
    assert "E-STATS-REPORTBY-UNKNOWN" in found


def test_a_non_list_report_by_is_refused_without_raising(write_config):
    """`validate.py` collects findings and never raises. `report_by` is a nested
    config value that new code reads, and this slice's predecessor shipped two
    crashes of exactly that kind — a scalar `statistics.contrasts` reaching
    `_check_sweep`, and an unhashable contrast `id` reaching a set."""
    for block in (5, True, "sex", {"sex": 1}):
        found = codes(
            write_config({"data.units": _UNITS_WITH_SEX, "statistics": {"report_by": block}})
        )
        assert "E-CONFIG-SHAPE" in found


def test_a_non_string_report_by_entry_is_refused(write_config):
    """A list is well-shaped but its *entries* may not be. An unhashable entry
    would reach a set membership test against `data.units.attributes`."""
    found = codes(
        write_config({"data.units": _UNITS_WITH_SEX, "statistics": {"report_by": [["sex"]]}})
    )
    assert "E-STATS-REPORTBY-UNKNOWN" in found


def test_a_thin_report_by_level_warns_before_the_run(write_config, tmp_path):
    """`reference.md` § Reporting strata: validate "warns when a level would hold
    fewer units than `limits.min_reported_n` — before the run rather than at
    disclosure." Counting is over *resolved* units, which is all validate can
    see; the realized count after attrition is `W-STATS-STRATUM-THIN`'s job at
    run time (Task 6)."""
    data = tmp_path / "data"
    data.mkdir()
    rows = "\n".join(f"p{i},{'f' if i <= 2 else 'm'}" for i in range(1, 13))
    (data / "index.csv").write_text(f"patient_id,sex\n{rows}\n")
    path = write_config(
        {
            "data.units": _UNITS_WITH_SEX,
            "data.input_dir": str(data),
            "limits": {"min_reported_n": 10},
            "statistics": {"report_by": ["sex"]},
        }
    )
    found = codes(path)
    assert "W-STATS-REPORTBY-THIN" in found
    message = messages_by_code(path)["W-STATS-REPORTBY-THIN"]
    assert "`f`" in message and "2 of 12" in message
    assert "`m`" not in message  # `m` holds 10, exactly at the floor — not below it


def test_two_thin_report_by_levels_are_diagnosed_in_a_stable_order(write_config, tmp_path):
    """Two levels below the floor must diagnose in level-sorted order, not roster
    order or set/dict iteration order. The roster here meets `m` before `f` —
    `m` is every one of the first three rows, `f` only the next two — so removing
    the `sorted(...)` in `_check_report_by` would surface `m` first: a mismatch
    this test catches deterministically, independent of `PYTHONHASHSEED`."""
    data = tmp_path / "data"
    data.mkdir()
    levels = ["m"] * 3 + ["f"] * 2 + ["x"] * 7
    rows = "\n".join(f"p{i},{levels[i - 1]}" for i in range(1, 13))
    (data / "index.csv").write_text(f"patient_id,sex\n{rows}\n")
    path = write_config(
        {
            "data.units": _UNITS_WITH_SEX,
            "data.input_dir": str(data),
            "limits": {"min_reported_n": 5},
            "statistics": {"report_by": ["sex"]},
        }
    )
    c = Collector()
    validate_config(path, c)
    thin = [f.message for f in c.findings if f.code == "W-STATS-REPORTBY-THIN"]
    assert thin == [
        "level `f` of `sex` would hold 2 of 12 units, below limits.min_reported_n (5)",
        "level `m` of `sex` would hold 3 of 12 units, below limits.min_reported_n (5)",
    ]


def test_a_non_list_hypotheses_block_is_refused_without_raising(write_config):
    """`validate.py` collects and never raises. S4c shipped two crashes from a
    nested config value reaching a reader, and `hypotheses` is a new one."""
    for block in (5, True, "h1", {"id": "h1"}):
        assert "E-CONFIG-SHAPE" in codes(write_config({"hypotheses": block}))


def test_a_hypothesis_with_compare_and_no_metric_is_refused(write_config):
    """`reference.md`: "a contrast reports a value per step metric, so the
    quantity under test is unnamed"."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {
                    "contrasts": [{"id": "x", "of": "method=spearman", "against": "baseline"}]
                },
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "compare": {"contrast": "x"},
                        "direction": "greater",
                        "threshold": 0.0,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-METRIC" in found


_TWO_SCOPE_EXPERIMENT = """\
from publishable import BaseExperiment, BaseStep


class Step01Measure(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {}


class Step02Combine(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {}


class CohortPilotExperiment(BaseExperiment):
    steps = [Step01Measure, Step02Combine]
"""


@pytest.fixture
def write_config_two_scopes(git_repo: Path, write_config):
    """`write_config`, but the entrypoint declares a repeat step and a summary
    step — so `validate` can tell which scope a hypothesis's metric belongs to.
    Modelled on `write_config_nondet`, which is the same pattern for a different
    step property."""

    def _write(overrides: dict | None = None) -> Path:
        path = write_config(overrides)
        write_experiment_module(git_repo, _TWO_SCOPE_EXPERIMENT)
        return path

    return _write


_THREE_SCOPE_EXPERIMENT = """\
from publishable import BaseExperiment, BaseStep


class Step01Measure(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {}


class Step02Fit(BaseStep):
    scope = "condition"

    def run(self, cfg, io):
        return {}


class Step03Combine(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {}


class CohortPilotExperiment(BaseExperiment):
    steps = [Step01Measure, Step02Fit, Step03Combine]
"""


@pytest.fixture
def write_config_three_scopes(git_repo: Path, write_config):
    """`write_config_two_scopes`, plus a `condition`-scoped step — needed to pin
    the bound-exists/inference-base scope gate's exact membership: `{"summary"}`
    is exempt, but `"condition"` is not, and no fixture declared a
    `condition`-scoped step until now, so a mutation widening the gate to also
    exempt `condition` scope had nothing in the suite to fail against it."""

    def _write(overrides: dict | None = None) -> Path:
        path = write_config(overrides)
        write_experiment_module(git_repo, _THREE_SCOPE_EXPERIMENT)
        return path

    return _write


def test_a_summary_metric_hypothesis_may_not_declare_compare(write_config_two_scopes):
    """`reference.md`: "a summary metric is one value per run, not a contrast
    between conditions — and a condition-step metric without `compare` is the
    same mistake inverted"."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step02_combine.agreement",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.9,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-FORM" in found


def test_a_condition_metric_hypothesis_must_declare_compare(write_config_two_scopes):
    """The same mistake inverted: a metric of a repeat-scoped step names a
    quantity that only exists per condition, so a hypothesis about it has to say
    which conditions it compares."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-FORM" in found


def test_a_hypothesis_naming_an_undeclared_step_is_refused_as_a_metric_fault(
    write_config_two_scopes,
):
    """A `metric` naming a step outside the entrypoint's `steps` list is folded
    into `E-HYPOTHESIS-METRIC`, the same code a missing metric gets, rather than
    a third identifier: in both cases the quantity under test does not exist."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step99_nonexistent.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-METRIC" in found
    assert "E-HYPOTHESIS-FORM" not in found


def test_a_mistyped_direction_is_refused_rather_than_silently_inverted(write_config_two_scopes):
    """Task 4 review: a `direction` outside `{greater, less}` was read as `less`
    and never echoed into the record, so a typo silently inverted the verdict.
    The refusal belongs at `validate` time, closing that gap for good."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greatr",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-DIRECTION" in found


def test_a_valid_direction_is_not_flagged(write_config_two_scopes):
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "less",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-DIRECTION" not in found


def test_a_mistyped_evaluate_on_is_refused_rather_than_silently_read_as_an_upper_bound(
    write_config_two_scopes,
):
    """`evaluate_on` is a documented enum (`observed | ci95_lower | ci95_upper`),
    but the evaluator reads anything other than `observed`/`ci95_lower` as
    `ci95_upper` — the same silent-misread shape as `direction`, so it gets the
    same refusal."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                        "evaluate_on": "ci95_lowerr",
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-EVALUATE-ON" in found


def test_a_valid_evaluate_on_is_not_flagged(write_config_two_scopes):
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                        "evaluate_on": "ci95_lower",
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-EVALUATE-ON" not in found


def test_a_hypothesis_entry_that_is_not_a_mapping_is_refused_as_a_metric_fault(write_config):
    """`hypotheses: [not-a-mapping]` is still a list — `_check_shape` has nothing to
    say about it — so `_check_hypotheses` must refuse a non-mapping entry itself
    rather than call `.get` on it, the same class of crash `_check_contrasts`
    guards against for `statistics.contrasts`."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": ["not-a-mapping"],
            }
        )
    )
    assert "E-HYPOTHESIS-METRIC" in found


def test_a_hypothesis_compared_to_baseline_needs_a_declared_baseline(write_config_two_scopes):
    """`reference.md` § Validation, "Hypothesis needs baseline":
    `hypotheses[0].compare.to: baseline` but `sweep.baseline` is not declared.
    Nothing populates a `vs_baseline` comparison without one, so the hypothesis
    would silently resolve to no observation rather than being refused up front."""
    found = codes(
        write_config_two_scopes(
            {
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BASELINE" in found


def test_a_hypothesis_compared_to_a_declared_baseline_is_not_flagged(write_config_two_scopes):
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BASELINE" not in found
    assert "E-HYPOTHESIS-COMPARE-TO" not in found


def test_a_hypothesis_compared_to_something_other_than_the_baseline_is_refused(
    write_config_two_scopes,
):
    """`compare.to` has one value. `hypotheses.resolve` never reads the field —
    it reads the `vs_baseline` block for the named condition whatever `to` says
    — so an unrefused `to: method=kendall` is evaluated against the baseline and
    the record shows a verdict for a comparison the config did not ask for. A
    claim against another *condition* is a `statistics.contrasts` entry, named
    through `compare.contrast`."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "method=kendall"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-COMPARE-TO" in found


def test_a_compare_to_naming_another_condition_gets_one_code_not_two(
    write_config_two_scopes,
):
    """`compare.to: method=kendall` with no `sweep.baseline` declared is a
    tempting way to have the widened `E-HYPOTHESIS-BASELINE` branch over-fire:
    naming *any* other condition through `condition` with no baseline declared
    looks like the bare-condition form this task refuses. It isn't — `to` here
    explicitly names a value other than `baseline`, which `E-HYPOTHESIS-COMPARE-TO`
    already refuses on its own, and firing `E-HYPOTHESIS-BASELINE` too would be
    the double-report one fault getting two codes exists to avoid, exactly as the
    baseline-itself case already guards against it for `E-HYPOTHESIS-CONDITION`."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": {"grid": {"analysis.method": ["spearman", "kendall"]}},
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "method=kendall"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-COMPARE-TO" in found
    assert "E-HYPOTHESIS-BASELINE" not in found


def test_a_sweep_without_a_baseline_still_needs_one_for_a_baseline_comparison(
    write_config_two_scopes,
):
    """The pair above varies two things at once — the whole `sweep` block *and*
    its `baseline` — so `has_baseline = bool(doc.get("sweep"))` passed the entire
    suite. This one holds `sweep` present, with a grid, and varies only
    `baseline`: under that mutant a config declaring a grid and no baseline
    validates clean and comes back `supported: null` after the full run, which is
    exactly the case `E-HYPOTHESIS-BASELINE` exists to refuse."""
    grid_only = {"grid": {"analysis.method": ["spearman"]}}
    hypothesis = {
        "id": "h",
        "kind": "confirmatory",
        "metric": "step01_measure.r",
        "compare": {"condition": "method=spearman", "to": "baseline"},
        "direction": "greater",
        "threshold": 0.5,
    }
    found = codes(write_config_two_scopes({"sweep": grid_only, "hypotheses": [hypothesis]}))
    assert "E-HYPOTHESIS-BASELINE" in found
    with_baseline = codes(
        write_config_two_scopes(
            {
                "sweep": {**grid_only, "baseline": {"analysis.method": "pearson"}},
                "hypotheses": [hypothesis],
            }
        )
    )
    assert "E-HYPOTHESIS-BASELINE" not in with_baseline


def test_a_compare_naming_a_condition_with_no_baseline_is_refused(write_config_two_scopes):
    """`compare: {condition: X}` with no `to` and no `sweep.baseline` used to fire
    neither check: `E-HYPOTHESIS-BASELINE` read `compare.get("to") == "baseline"`,
    which is `False` with no `to` key at all, and `E-HYPOTHESIS-CONDITION` never
    fires because `method=spearman` is a label the grid-only sweep below genuinely
    declares — it resolves cleanly, it just resolves to nothing to compare
    against. `reference.md` § Pre-registration's ruling is to refuse this rather
    than default the missing side to `baseline`."""
    grid_only = {"grid": {"analysis.method": ["spearman"]}}
    found = codes(
        write_config_two_scopes(
            {
                "sweep": grid_only,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BASELINE" in found


def test_a_bare_compare_condition_with_a_declared_baseline_is_not_flagged(
    write_config_two_scopes,
):
    """The ruling refuses the form with *no* baseline anywhere to name — not the
    bare `{condition: X}` spelling itself. Once `sweep.baseline` is declared,
    `hypotheses.resolve` has a `vs_baseline` block to read whether or not `to`
    spells out that it's the baseline being compared against, so this must stay
    clean; an over-broad check that refused every bare `condition` regardless of
    a declared baseline would wrongly flag it."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BASELINE" not in found


def test_a_hypothesis_naming_an_undeclared_condition_is_refused(write_config_two_scopes):
    """`_check_contrasts` resolves `of`/`against` against `expand(doc)`'s labels;
    nothing did the same for `compare.condition`. A typo'd label validated clean,
    `hypotheses.resolve` looked it up and found nothing, and the verdict read
    `observed: null, supported: null` with nothing saying why."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearmen", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-CONDITION" in found


def test_a_hypothesis_naming_the_baseline_itself_is_refused(write_config_two_scopes):
    """`vs_baseline` holds one entry per *other* condition — a baseline has no
    comparison against itself — so naming it resolves to no observation exactly
    as a typo does, and gets the same code."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "baseline", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-CONDITION" in found


def test_a_hypothesis_naming_a_declared_condition_is_not_flagged(write_config_two_scopes):
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-CONDITION" not in found


def test_a_sweep_expand_cannot_read_leaves_the_condition_unchecked_rather_than_raising(
    write_config_two_scopes,
):
    """`validate` collects and never raises. `expand` raises `TypeError` on an
    axis whose values are a scalar rather than a list — `_check_sweep`'s finding
    to make — so the label test skips instead of turning one bad indent into a
    traceback out of `validate_config`."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": "spearman"},
                },
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-CONDITION" not in found
    assert found  # the sweep's own shape finding, not silence


def test_a_hypothesis_kind_outside_the_two_is_refused(write_config_two_scopes):
    """The third member of the `direction`/`evaluate_on` triple, and the one with
    no runtime guard at all: `_is_counted` tests `== "confirmatory"`, so
    `confirmatry` — or an omitted `kind` — drops a pre-registered claim out of its
    correction family and decides it on the raw, *tighter* bound. The error
    direction is over-support, so an absent `kind` is refused rather than
    defaulted."""
    for kind in ("confirmatry", None):
        hypothesis = {
            "id": "h",
            "metric": "step01_measure.r",
            "compare": {"condition": "method=spearman", "to": "baseline"},
            "direction": "greater",
            "threshold": 0.5,
        }
        if kind is not None:
            hypothesis["kind"] = kind
        found = codes(
            write_config_two_scopes(
                {
                    "sweep": _TWO_CONDITIONS,
                    "hypotheses": [hypothesis],
                }
            )
        )
        assert "E-HYPOTHESIS-KIND" in found


def test_both_declared_kinds_are_accepted(write_config_two_scopes):
    for kind in ("confirmatory", "exploratory"):
        found = codes(
            write_config_two_scopes(
                {
                    "sweep": _TWO_CONDITIONS,
                    "hypotheses": [
                        {
                            "id": "h",
                            "kind": kind,
                            "metric": "step01_measure.r",
                            "compare": {"condition": "method=spearman", "to": "baseline"},
                            "direction": "greater",
                            "threshold": 0.5,
                        }
                    ],
                }
            )
        )
        assert "E-HYPOTHESIS-KIND" not in found


def test_a_hypothesis_with_no_direction_is_refused(write_config_two_scopes):
    """`verdict_for` sets `supported` only for `greater`/`less`, so an omitted
    `direction` behaves exactly as a typo'd one — `supported: null` after the
    whole run, with nothing in the record saying why. Same field, same code."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-DIRECTION" in found


def test_a_missing_or_non_numeric_threshold_is_refused(write_config_two_scopes):
    """`verdict_for` compares against an `int`/`float` that is not a `bool` and
    nothing else, so a missing threshold — or `true`, or a string — is a
    pre-registered claim that comes back unevaluated. `E-HYPOTHESIS-THRESHOLD`
    mirrors that predicate exactly, so validate refuses what the evaluator
    declines to judge."""
    for threshold in (None, True, "0.5"):
        hypothesis = {
            "id": "h",
            "kind": "confirmatory",
            "metric": "step01_measure.r",
            "compare": {"condition": "method=spearman", "to": "baseline"},
            "direction": "greater",
        }
        if threshold is not None:
            hypothesis["threshold"] = threshold
        found = codes(
            write_config_two_scopes(
                {
                    "sweep": _TWO_CONDITIONS,
                    "hypotheses": [hypothesis],
                }
            )
        )
        assert "E-HYPOTHESIS-THRESHOLD" in found


def test_a_zero_threshold_is_accepted(write_config_two_scopes):
    """`reference.md`'s own superiority form is `threshold: 0.0` — the check is a
    type test, not a truthiness test."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.0,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-THRESHOLD" not in found


def test_a_hypothesis_naming_an_undeclared_contrast_is_refused(write_config_two_scopes):
    """`reference.md` § Validation, "Hypothesis names a real contrast":
    `hypotheses[1].compare.contrast` is `invariance`, which `statistics.contrasts`
    does not declare."""
    found = codes(
        write_config_two_scopes(
            {
                "statistics": {
                    "contrasts": [{"id": "x", "of": "method=spearman", "against": "baseline"}]
                },
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"contrast": "invariance"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-CONTRAST" in found


def test_a_hypothesis_naming_a_declared_contrast_is_not_flagged(write_config_two_scopes):
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {
                    "contrasts": [{"id": "x", "of": "method=spearman", "against": "baseline"}]
                },
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"contrast": "x"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-CONTRAST" not in found


def test_a_declared_contrast_needs_no_baseline_even_under_a_grid_only_sweep(
    write_config_two_scopes,
):
    """A pure `compare: {contrast: x}` hypothesis resolves entirely through
    `statistics.contrasts` — `hypotheses.resolve` never reaches `vs_baseline` for
    it — so it must stay clean even when `sweep.baseline` is undeclared. The other
    contrast test declares a baseline via `_TWO_CONDITIONS`, which leaves the
    widened `E-HYPOTHESIS-BASELINE` branch (added for the bare-`condition` form)
    untested against the pure-contrast form under exactly the sweep shape that
    would trip it if the branch ever grew to include `contrast`."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": {"grid": {"analysis.method": ["spearman", "kendall"]}},
                "statistics": {
                    "contrasts": [
                        {"id": "x", "of": "method=spearman", "against": "method=kendall"}
                    ]
                },
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"contrast": "x"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BASELINE" not in found


def test_a_contrast_alongside_condition_needs_no_baseline_either(write_config_two_scopes):
    """`hypotheses.resolve` checks `"contrast" in compare` first and returns from
    that branch without ever reading `condition` — so a hypothesis naming both
    resolves through the contrast, never through `vs_baseline`, and needs no
    declared baseline regardless of what `condition` says. Without the `contrast
    not in compare` exclusion on the widened branch, this config would be refused
    for a baseline comparison it was never going to make."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": {"grid": {"analysis.method": ["spearman", "kendall"]}},
                "statistics": {
                    "contrasts": [
                        {"id": "x", "of": "method=spearman", "against": "method=kendall"}
                    ]
                },
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"contrast": "x", "condition": "method=spearman"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BASELINE" not in found


def test_a_bound_hypothesis_is_refused_when_no_metric_could_carry_an_interval(
    write_config_two_scopes,
):
    """`reference.md` § Validation, "Hypothesis bound exists": `evaluate_on` names
    a bound, but `data.units` is undeclared and template `generic` defines no
    `aggregate` (checked directly: `GenericTemplate` does not override
    `BaseTemplate.aggregate`), so no metric this run computes can carry an
    interval — `write_config`'s base document never declares `data.units`.
    `sweep: _TWO_CONDITIONS` declares a baseline so this fixture doesn't also
    trip `E-HYPOTHESIS-BASELINE`, keeping the assertion isolated to one rule.
    The metric is `step01_measure.r`, a `repeat`-scoped step, deliberately not
    the `summary`-scoped `step02_combine.agreement`: a summary metric could be
    a `reported: true` `Estimate` core never inspects the step body to rule
    out, and `reference.md` (§ What a hypothesis is tested against) says that
    per-metric exception is "settled when the step returns", not here — a
    `repeat`-scoped metric has no such exception, so this fixture can't be read
    as accidentally exercising it."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                        "evaluate_on": "ci95_lower",
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BOUND" in found


def test_a_bound_hypothesis_is_not_flagged_once_units_are_declared(write_config_two_scopes):
    """The discriminating half of the bound-exists rule: once `data.units` is
    declared, a metric derived over the unit table can carry an interval, so the
    same `evaluate_on: ci95_lower` no longer names an impossible bound."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                        "evaluate_on": "ci95_lower",
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BOUND" not in found


def test_a_hypothesis_with_no_inference_base_warns_rather_than_refuses(
    write_config_two_scopes,
):
    """`reference.md` § Validation, "Hypothesis has an inference base": the same
    impossible-interval condition as the bound-exists rule, but with no bound
    requested — a config that would otherwise be fine, since `evaluate_on` is
    absent. Every metric will be `basis: repeats`: reportable, but not testable
    against an interval. `step01_measure.r`, not `step02_combine.agreement`, for
    the same reason the bound-exists fixture above avoids the summary step: a
    `repeat`-scoped metric can never be a `reported: true` `Estimate`, so
    "every metric will be `basis: repeats`" is unambiguously true of it."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "W-HYPOTHESIS-INFERENCE-BASE" in found
    assert "E-HYPOTHESIS-BOUND" not in found


def test_a_hypothesis_with_an_inference_base_is_not_warned(write_config_two_scopes):
    """Once `data.units` is declared, the same hypothesis has a real inference
    base — the warning is specific to the case where none exists."""
    found = codes(
        write_config_two_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                    }
                ],
            }
        )
    )
    assert "W-HYPOTHESIS-INFERENCE-BASE" not in found


def test_a_summary_metric_bound_is_not_refused_even_with_no_units(write_config_two_scopes):
    """`reference.md` § What a hypothesis is tested against: a `scope: "summary"`
    metric can be a `reported: true` `Estimate` a step supplies directly, with
    its own real `ci95` and no unit table involved — core never inspects the
    step body to know whether *this* one does. `command_run` treats
    `E-HYPOTHESIS-BOUND` as a hard stop, so applying the two-condition
    (`data.units` undeclared, template has no `aggregate`) test to a
    `scope: "summary"` metric would permanently refuse a design the spec
    explicitly permits (`A hypothesis may name a summary metric`), not merely
    defer it — so the bound-exists check does not fire for one, and neither
    does the inference-base warning."""
    found = codes(
        write_config_two_scopes(
            {
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step02_combine.agreement",
                        "direction": "greater",
                        "threshold": 0.99,
                        "evaluate_on": "ci95_lower",
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BOUND" not in found
    assert "W-HYPOTHESIS-INFERENCE-BASE" not in found


def test_a_summary_metric_hypothesis_gets_no_inference_base_warning(write_config_two_scopes):
    """The scope gate on `W-HYPOTHESIS-INFERENCE-BASE` is justified by the
    warning's own premise, not the error's hard-stop argument (a warning never
    stops a run) — "every metric will be `basis: repeats`" is false for a
    `scope: "summary"` metric that turns out to be a `reported: true`
    `Estimate`: it is `reported`, carries its own interval, and is exactly what
    `evaluate_on` can test. No `evaluate_on` here (unlike the bound-exists
    fixture above), so this exercises the warning branch specifically rather
    than the error branch."""
    found = codes(
        write_config_two_scopes(
            {
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step02_combine.agreement",
                        "direction": "greater",
                        "threshold": 0.9,
                    }
                ],
            }
        )
    )
    assert "W-HYPOTHESIS-INFERENCE-BASE" not in found
    assert "E-HYPOTHESIS-BOUND" not in found


def test_a_dotless_metric_is_refused_once_even_when_it_names_a_real_step(
    write_config_two_scopes,
):
    """`metric.partition(".")` on a dotless value like `step01_measure` returns
    `("step01_measure", "", "")` — `step` still resolves to the real, declared
    `repeat`-scoped step, even though `name` is empty and the metric is
    definitely malformed (no `.metric` half to name a quantity with). Before
    the bound/warning block was moved behind the `metric_is_well_formed` guard,
    this let it read that real `scope` and fire `E-HYPOTHESIS-BOUND` (or the
    warning) *alongside* `E-HYPOTHESIS-METRIC`, reporting one fault under two
    codes — the double-report `_check_hypotheses`'s own docstring says a
    hypothesis with two *distinct* faults should report, but a single
    malformed `metric` is one fault, not two."""
    found = codes(
        write_config_two_scopes(
            {
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step01_measure",
                        "direction": "greater",
                        "threshold": 0.5,
                        "evaluate_on": "ci95_lower",
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-METRIC" in found
    assert "E-HYPOTHESIS-BOUND" not in found
    assert "W-HYPOTHESIS-INFERENCE-BASE" not in found


def test_a_condition_scoped_bound_is_still_refused(write_config_three_scopes):
    """The scope gate exempts exactly `{None, "summary"}`, not "anything but
    `repeat`" — a `scope: "condition"` metric has no reported-`Estimate`
    exception either (that mechanism is `summary`-only), so the bound-exists
    check must still fire for one. Needs `write_config_three_scopes`: no
    existing fixture declared a `condition`-scoped step, so a mutation that
    widened the gate to also exempt `condition` scope had nothing in the suite
    to catch it."""
    found = codes(
        write_config_three_scopes(
            {
                "sweep": _TWO_CONDITIONS,
                "hypotheses": [
                    {
                        "id": "h",
                        "kind": "confirmatory",
                        "metric": "step02_fit.score",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater",
                        "threshold": 0.5,
                        "evaluate_on": "ci95_lower",
                    }
                ],
            }
        )
    )
    assert "E-HYPOTHESIS-BOUND" in found


def test_a_baseline_fixing_every_axis_of_a_crossed_grid_warns_before_the_run(write_config):
    """`reference.md` § Validation, "Baseline leaves contrasts confounded":
    `sweep.baseline` "fixes a value on every axis ... so 2 of 3 contrasts differ
    on both and are reported `confounded: true`". `cli.py` marks each such
    comparison at run time, after the compute is spent; the declaration alone
    decides it, so `validate` says it first.

    Two axes of two values each, against a baseline fixing both to values the
    grid does not repeat: every cell differs from the baseline on the method
    axis, and the two carrying the raised `min_samples` differ on both."""
    path = write_config(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
                "grid": {
                    "analysis.method": ["spearman", "kendall"],
                    "analysis.min_samples": [10, 20],
                },
            }
        }
    )
    found = codes(path)
    assert "W-SWEEP-BASELINE-CONFOUNDED" in found
    message = messages_by_code(path)["W-SWEEP-BASELINE-CONFOUNDED"]
    assert "2 of 4 baseline comparisons" in message
    assert "`method=spearman__min_samples=20`" in message
    assert "`analysis.method`" in message and "`analysis.min_samples`" in message
    # The remedy, which only per-cell targeting made true: freeing the
    # stratifying axis now gives each cell its own baseline, and the freed axis
    # stops appearing in `differs_on` at all. Task 7 deliberately left this out
    # while `resolve_contrasts` targeted the first baseline for every condition.
    assert "leave the ones you are stratifying over free" in message


def test_a_partly_fixed_baseline_is_silent_while_its_run_marks_confounded(write_config):
    """Why § Warnings core reports still says silence here "is not a verdict that
    such a design confounds nothing", after per-cell targeting.

    The guard is "the baseline fixes every swept axis". A baseline fixing two of
    three leaves the third free, so this warning stays silent — while the cells that
    move both fixed axes differ from *their own cell's* baseline on both and are
    marked `confounded: true` at run time. Per-cell targeting removes the free axis
    from `differs_on`; it does not remove a difference on two fixed ones, so the
    caution is still the honest phrasing and is deliberately not softened."""
    path = write_config(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "analysis.min_samples": [10, 20],
                    "analysis.confidence": [0.95, 0.99],
                },
            }
        }
    )
    assert "W-SWEEP-BASELINE-CONFOUNDED" not in codes(path)

    from publishable.contrasts import differing_axes, resolve_contrasts
    from publishable.sweep import expand

    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "analysis.min_samples": [10, 20],
                    "analysis.confidence": [0.95, 0.99],
                },
            }
        }
    )
    by_index = {c.index: c for c in conditions}
    differing = [
        differing_axes(by_index[m.of], by_index[m.against])
        for m in resolve_contrasts({}, conditions)
    ]
    assert all("analysis.confidence" not in axes for axes in differing)
    assert [axes for axes in differing if len(axes) > 1] == [
        ["analysis.method", "analysis.min_samples"],
        ["analysis.method", "analysis.min_samples"],
    ]


def test_a_half_fixed_paired_axis_is_silent_with_nothing_expanded_and_a_confounded_run(
    write_config,
):
    """The second silent shape § Warnings core reports now names, and the one whose
    mechanism differs from the row's per-cell sentence.

    A baseline fixing *some* of a multi-path `paired` axis's paths counts that
    axis fixed (`sweep._baseline_cells` reads fixedness off the cells' paths and
    takes any match), so nothing expands per cell — there is exactly ONE baseline,
    not one per cell. Both comparisons against it differ on `analysis.min_samples`
    *and* on `analysis.confidence`, which the baseline leaves alone, so the run
    marks them `confounded: true` while `validate` says nothing. The row explained
    that silence by per-cell expansion, which is false here; the three assertions
    below are the three halves of the correction."""
    sweep = {
        "baseline": {"analysis.min_samples": 30},
        "paired": [
            {"analysis.min_samples": 10, "analysis.confidence": 0.9},
            {"analysis.min_samples": 20, "analysis.confidence": 0.8},
        ],
    }
    assert "W-SWEEP-BASELINE-CONFOUNDED" not in codes(write_config({"sweep": sweep}))

    from publishable.contrasts import differing_axes, resolve_contrasts

    conditions = expand({"sweep": sweep})
    assert [c.index for c in conditions if c.is_baseline] == [0]  # nothing expanded

    by_index = {c.index: c for c in conditions}
    differing = [
        differing_axes(by_index[m.of], by_index[m.against])
        for m in resolve_contrasts({}, conditions)
    ]
    assert differing == [
        ["analysis.min_samples", "analysis.confidence"],
        ["analysis.min_samples", "analysis.confidence"],
    ]


def test_a_crossed_grid_whose_cells_each_differ_once_is_not_confounded(write_config):
    """The threshold is *more than one* differing axis, not *more than none*. A
    two-axis grid whose second axis holds only the baseline's own value produces
    cells differing in exactly one place — interpretable contrasts, and the
    design `allocation` and `sweep.baseline` are meant to produce. A check that
    warned here would fire on every baseline-plus-grid config in the repo."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
                    "grid": {
                        "analysis.method": ["pearson", "spearman"],
                        "analysis.min_samples": [10],
                    },
                }
            }
        )
    )
    assert "W-SWEEP-BASELINE-CONFOUNDED" not in found  # the baseline fixes both axes


def test_a_single_axis_sweep_is_never_confounded(write_config):
    """The worked example's own shape: one swept axis, so no comparison can
    differ on two. `test_a_normal_baseline_plus_grid_config_still_validates_clean`
    asserts the whole config is clean; this one names the code, so a widened
    check is diagnosed rather than showing up as a distant fixture failure."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                }
            }
        )
    )
    assert "W-SWEEP-BASELINE-CONFOUNDED" not in found


_UNITS_WITH_DX = {"from": "index.csv", "key": "patient_id", "attributes": ["dx_family"]}


def _roster_with_dx(tmp_path: Path, rare: int, total: int = 12) -> Path:
    """An `index.csv` carrying one attribute, `rare` of whose units are `rare`.

    The same shape `test_a_thin_report_by_level_warns_before_the_run` writes for
    `sex`, under its own directory so `data.input_dir` still resolves outside the
    repo."""
    data = tmp_path / "dx"
    data.mkdir()
    levels = ["rare"] * rare + ["common"] * (total - rare)
    rows = "\n".join(f"p{i},{levels[i - 1]}" for i in range(1, total + 1))
    (data / "index.csv").write_text(f"patient_id,dx_family\n{rows}\n")
    return data


_ONE_AXIS_SWEEP = {
    "baseline": {"analysis.method": "pearson"},
    "grid": {"analysis.method": ["spearman"]},
}


def _contrast_within(level: str) -> list:
    return [
        {
            "id": "stratified",
            "of": "method=spearman",
            "against": "baseline",
            "within": {"dx_family": level},
        }
    ]


def test_a_thin_contrast_stratum_warns_before_the_run(write_config, tmp_path):
    """`reference.md` § Validation, "Contrast stratum is populated":
    `contrasts[1].within: {dx_family: rare}` "leaves 6 paired units; below
    `limits.min_reported_n` (warning)". Counting is over *resolved roster* units
    matching the stratum, which is all `validate` sees — `n_paired` at run time
    is that intersection after attrition, so it can only be smaller."""
    path = write_config(
        {
            "data.units": _UNITS_WITH_DX,
            "data.input_dir": str(_roster_with_dx(tmp_path, rare=2)),
            "limits": {"min_reported_n": 10},
            "sweep": _ONE_AXIS_SWEEP,
            "statistics": {"contrasts": _contrast_within("rare")},
        }
    )
    found = codes(path)
    assert "W-STATS-CONTRAST-THIN" in found
    message = messages_by_code(path)["W-STATS-CONTRAST-THIN"]
    assert "`dx_family=rare`" in message
    assert "2 of 12 units" in message


def test_a_populated_contrast_stratum_does_not_warn(write_config, tmp_path):
    """Exactly at the floor is not below it — the same boundary
    `W-STATS-REPORTBY-THIN`'s `m` level pins. Without this, a check that dropped
    the comparison and always warned would pass its own positive test."""
    path = write_config(
        {
            "data.units": _UNITS_WITH_DX,
            "data.input_dir": str(_roster_with_dx(tmp_path, rare=10)),
            "limits": {"min_reported_n": 10},
            "sweep": _ONE_AXIS_SWEEP,
            "statistics": {"contrasts": _contrast_within("rare")},
        }
    )
    found = codes(path)
    assert "E-STATS-CONTRAST-WITHIN" not in found  # the attribute is declared
    assert "W-STATS-CONTRAST-THIN" not in found


def test_an_unknown_within_attribute_is_refused_without_also_being_called_thin(
    write_config, tmp_path
):
    """One typo, one finding. An undeclared attribute matches no unit, so the
    thinness count would report `0 of 12` beside `E-STATS-CONTRAST-WITHIN` and
    send the reader looking for missing units instead of a misspelled name."""
    path = write_config(
        {
            "data.units": _UNITS_WITH_DX,
            "data.input_dir": str(_roster_with_dx(tmp_path, rare=2)),
            "limits": {"min_reported_n": 10},
            "sweep": _ONE_AXIS_SWEEP,
            "statistics": {
                "contrasts": [
                    {
                        "id": "stratified",
                        "of": "method=spearman",
                        "against": "baseline",
                        "within": {"dx_familly": "rare"},
                    }
                ]
            },
        }
    )
    found = codes(path)
    assert "E-STATS-CONTRAST-WITHIN" in found
    assert "W-STATS-CONTRAST-THIN" not in found


def test_a_string_min_reported_n_does_not_crash_the_contrast_stratum_count(write_config, tmp_path):
    """The same silent-skip-or-crash class `test_a_string_min_reported_n_is_reported`
    pins one guard over in `_check_report_by`: a leaf type fault is deliberately
    non-fatal, so `_check_contrasts` still runs on a doc holding a `str` floor,
    and `len(matched) < floor` would raise `TypeError` out of a module whose
    contract is that it collects. The envelope reports the type; nothing else
    does."""
    path = write_config(
        {
            "data.units": _UNITS_WITH_DX,
            "data.input_dir": str(_roster_with_dx(tmp_path, rare=2)),
            "limits": {"min_reported_n": "ten"},
            "sweep": _ONE_AXIS_SWEEP,
            "statistics": {"contrasts": _contrast_within("rare")},
        }
    )
    found = codes(path)
    assert "E-CONFIG-TYPE" in found
    assert "W-STATS-CONTRAST-THIN" not in found


def test_a_glob_source_with_a_declared_attribute_is_reported_by_validate(write_config):
    """The unit-level refusal has to arrive as a *finding*: `_check_units` catches
    `ContractError` out of `resolve_units`, so a glob that cannot supply a declared
    attribute is a diagnostic rather than a traceback."""
    path = write_config(
        {"data.units": {"from": {"glob": "*.csv"}, "key": "path", "attributes": ["label"]}}
    )
    assert "E-UNITS-ATTR-MISSING" in codes(path)


def test_a_moved_template_version_names_a_parameter_the_config_leaves_unset(write_config):
    """§ Validation's "Template version moved" row reports two things — the moved
    version and `request.timeout` being new and unset. Only the first was reported,
    so the warning said where to look without saying what to look at."""
    path = write_config({"template_version": "0.9.0", "parameters.analysis.confidence": _DELETE})
    c = Collector()
    validate_config(path, c)
    warnings = [f for f in c.findings if f.code == "W-TEMPLATE-VERSION"]
    assert len(warnings) == 1
    assert "analysis.confidence" in warnings[0].message
    assert "analysis.method" not in warnings[0].message


def test_an_unset_parameter_is_named_only_when_the_version_moved(write_config):
    """The naming is gated on the mismatch: a config matching the installed version
    draws no warning at all, so a defaulted parameter it omits is not reported."""
    path = write_config({"parameters.analysis.confidence": _DELETE})
    assert "W-TEMPLATE-VERSION" not in codes(path)


def test_the_inapplicable_correction_warning_asserts_nothing_about_null_test(write_config):
    """A config declaring `statistics.null_test` reaches this warning — the block is
    refused (`E-STATS-NULLTEST-UNSUPPORTED`) but `validate` collects rather than
    stopping — and the message used to tell that config its `null_test` was
    undeclared. The condition is unchanged and still over-broad against the row it
    implements; what this pins is only that the message asserts nothing false."""
    path = write_config(
        {
            "sweep": _TWO_CONDITIONS,
            "statistics": {"correction": "fdr_bh", "null_test": {"shuffle": "label"}},
        }
    )
    c = Collector()
    validate_config(path, c)
    found = {f.code: f.message for f in c.findings}
    assert "E-STATS-NULLTEST-UNSUPPORTED" in found
    assert "undeclared" not in found["W-STATS-CORRECTION-INAPPLICABLE"]


def test_a_sample_only_sweep_is_not_a_correction_family(write_config):
    """§ Validation, "Correction declared for a family": the warning is "not raised
    for a `sample`-only sweep, whose draws aren't a family". That exception was
    unreachable while `sample` was refused, and is live now. It holds
    structurally rather than by a special case: `resolve_contrasts` compares
    every condition against a *declared* baseline, and a `sample`-only sweep
    declares none, so there are no comparisons to correct."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "sample": {"n": 6, "ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}}}
                },
                "statistics": {"correction": "none"},
            }
        ),
        c,
    )
    assert not c.findings, [f.code for f in c.findings]


def test_a_baseline_beside_a_sampled_axis_is_refused(write_config):
    """§ Sweeps and repeats: the correction family "counts conditions from `grid`,
    `paired`, `ablate`, and `groups`, and skips `sample`". Nothing implements that
    exclusion, so every draw beside a declared baseline becomes a comparison and
    every interval is corrected against a family several times the documented size.
    `E-SWEEP-SAMPLE-BASELINE` refuses the combination until the family excludes
    drawn conditions.

    This is the decision the previous version of this test invited: it pinned the
    doubling "as the behaviour that ships, not as the behaviour that is wanted",
    and said "if a later slice warns or refuses, this test is where the decision
    lands". It lands here. The expansion assertions below are kept unchanged
    — `expand` is not what moved, and § Expansion modes' rule that a baseline
    expands over the axes it does not fix still holds of a `sample` axis."""
    path = write_config(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "sample": {"n": 6, "ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}}},
            }
        }
    )
    assert codes(path) == {"E-SWEEP-SAMPLE-BASELINE"}

    conditions = expand(yaml.safe_load(path.read_text()))
    assert [c.is_baseline for c in conditions] == [True] * 6 + [False] * 6
    # Each baseline carries its own draw, and the draws are the same six values.
    assert [c.values["analysis.confidence"] for c in conditions[:6]] == [
        c.values["analysis.confidence"] for c in conditions[6:]
    ]


def test_a_uniform_range_over_an_int_parameter_is_refused_by_what_it_draws(write_config):
    """The bounds are two legal integers, so a bounds-only check reports nothing —
    and the draw is `118.38…`, which a step reads where `parameter_spec` declares
    `int`. § Validation's "Types" row promises to refuse exactly that, and the
    value that executes is the drawn one, not the bound."""
    c = Collector()
    validate_config(
        write_config(
            {
                "sweep": {
                    "sample": {
                        "n": 4,
                        "ranges": {"analysis.min_samples": {"uniform": [10, 200]}},
                    }
                }
            }
        ),
        c,
    )
    found = [f for f in c.findings if f.code == "E-PARAM-VALUE"]
    assert found, [f.code for f in c.findings]
    assert found[0].path == "sweep.sample.ranges.analysis.min_samples.uniform"
    assert "expected integer" in found[0].message
    assert "int_uniform" in found[0].message
    # One mistake, one finding — not one per drawn condition.
    assert len(found) == 1


def test_a_sampled_value_outside_the_parameters_choices_is_refused(write_config):
    """The other half of the same class, and the one a form-level rule could not
    catch: both `int_uniform` endpoints are declared choices, the form is right
    for an `int` parameter, and the draws in between are not choices at all."""
    from publishable.param import Param
    from publishable.templates.builtin.generic import GenericTemplate

    original = GenericTemplate.parameter_spec
    GenericTemplate.parameter_spec = {
        **original,
        "analysis.min_samples": Param(int, default=10, choices=[10, 50]),
    }
    try:
        c = Collector()
        validate_config(
            write_config(
                {
                    "parameters.analysis": {
                        "method": "pearson",
                        "min_samples": 10,
                        "confidence": 0.95,
                        "drop_missing": True,
                    },
                    "sweep": {
                        "sample": {
                            "n": 8,
                            "ranges": {"analysis.min_samples": {"int_uniform": [10, 50]}},
                        }
                    },
                }
            ),
            c,
        )
        found = [f for f in c.findings if f.code == "E-PARAM-VALUE"]
        assert found, [f.code for f in c.findings]
        assert "expected one of 10, 50" in found[0].message
    finally:
        GenericTemplate.parameter_spec = original


def test_a_well_typed_sample_draws_no_value_findings(write_config):
    """The mirror: `int_uniform` over an `int` parameter and `uniform` over a
    float one draw legal values, and neither reports anything."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "sample": {
                        "n": 16,
                        "ranges": {
                            "analysis.min_samples": {"int_uniform": [10, 200]},
                            "analysis.confidence": {"uniform": [0.80, 0.99]},
                        },
                    }
                }
            }
        )
    )
    assert "E-PARAM-VALUE" not in found


def test_a_sample_sweep_with_no_baseline_stays_legal(write_config):
    """The refusal above is scoped to the combination that inflates the family, and
    this is the shape it must not touch: `resolve_contrasts` generates a comparison
    only against a *declared* baseline, so a sample-only sweep produces none and
    nothing is corrected against anything. A refusal wider than the harm would
    strand `sample` for the dose-response designs § Expansion modes shows it for."""
    path = write_config(
        {
            "sweep": {
                "sample": {
                    "n": 4,
                    "seed": 7,
                    "ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}},
                }
            }
        }
    )
    assert codes(path) == set()
    assert len(expand(yaml.safe_load(path.read_text()))) == 4


def test_a_declared_contrast_over_a_sample_sweep_stays_legal(write_config):
    """A declared `statistics.contrasts` entry names its two sides, so it adds
    exactly the members the user asked for rather than one per drawn condition.
    The refusal is about the *generated* family, and this pins that it does not
    reach a declared one."""
    doc_path = write_config(
        {
            "sweep": {
                "sample": {
                    "n": 2,
                    "seed": 7,
                    "ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}},
                }
            }
        }
    )
    doc = yaml.safe_load(doc_path.read_text())
    labels = [c.label for c in expand(doc)]
    doc["statistics"] = {
        "contrasts": [{"id": "hi_vs_lo", "of": labels[0], "against": labels[1]}]
    }
    doc_path.write_text(yaml.safe_dump(doc))
    assert not [c for c in codes(doc_path) if c.startswith("E-")]


def test_a_baseline_beside_a_grid_is_untouched_by_the_sample_refusal(write_config):
    """The neighbouring shape the refusal must leave alone: a baseline over an
    enumerated axis is the ordinary design, its comparisons are the family the
    document counts, and nothing here changed."""
    assert codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson"},
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                }
            }
        )
    ) == set()


# --- `data.units.weight_by` ------------------------------------------------
#
# Every one of these asserts its OWN identifier rather than "some finding":
# these checks ran beside a blanket refusal of the whole declaration for most of
# their life, and a test asserting only that something was reported would have
# passed off that refusal and said nothing about the check under it.


def _weighted_table(tmp_path: Path, body: str, column: str = "sampling_weight") -> None:
    """Write the roster these checks read, into the directory `write_config` points
    `data.input_dir` at. Writing it anywhere else is how a probe comes back empty
    for every input, including the one that had to fail."""
    (tmp_path / "input" / "index.csv").write_text(f"patient_id,{column}\n{body}")


def test_a_weight_by_naming_no_attribute_is_reported(write_config, tmp_path):
    """§ Validation, "Weight attribute exists": `weight_by` names
    `sampling_weight`, which is not a unit
    attribute. `attributes` is the reference set — `weight_by` has to survive
    resolution to be read per unit at analysis time."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "weight_by": "sampling_weight"}}
    )
    assert "E-DATA-WEIGHT-UNKNOWN" in codes(path)


def test_a_declared_weight_attribute_is_not_reported_unknown(write_config, tmp_path):
    """The second half of the same declaration: declaring the attribute is what
    makes the name check pass, so the check is discriminating rather than
    reporting on every `weight_by` there is."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
                "weight_by": "sampling_weight",
            }
        }
    )
    found = codes(path)
    assert "E-DATA-WEIGHT-UNKNOWN" not in found
    assert "E-DATA-WEIGHT-INVALID" not in found


def test_an_empty_weight_by_is_a_finding_not_a_default(write_config):
    """Decision 3, the second truthiness hole: an empty declaration changes no
    behavior, and silently reading it as "unset" makes the config lie.

    The message is asserted, not only the code: `''` is also "not a unit
    attribute", so the name check below reports the same identifier for it and a
    code-only assertion cannot tell the two branches apart. What an empty
    declaration needs said is that it is empty — telling a reader that `''` is
    not among the declared attributes sends them to the wrong list."""
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "weight_by": ""}}
    )
    found = messages_by_code(path)
    assert "E-DATA-WEIGHT-UNKNOWN" in found
    assert "is empty" in found["E-DATA-WEIGHT-UNKNOWN"]


def test_a_non_string_weight_by_is_left_to_the_envelope(write_config):
    """`envelope.LEAF_TYPES` types `data.units.weight_by` a `str`, so a number is
    already `E-CONFIG-TYPE`. Reporting it a second time as "empty" would both
    duplicate the finding and describe `3` with a word that does not fit it."""
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "weight_by": 3}}
    )
    found = codes(path)
    assert "E-CONFIG-TYPE" in found
    assert "E-DATA-WEIGHT-UNKNOWN" not in found


def test_the_name_check_still_runs_with_no_roster(write_config, tmp_path):
    """The value half needs a roster; the name half does not, and reads the
    declaration alone. Pinned with a resolvable-shaped config whose `input_dir`
    is relative — `_check_units` returns `None` there — so this is a reachable
    skip rather than the silent-skip class."""
    path = write_config(
        {
            "data.input_dir": "input",
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "weight_by": "sampling_weight",
            },
        }
    )
    assert "E-DATA-WEIGHT-UNKNOWN" in codes(path)


def test_a_zero_weight_is_refused(write_config, tmp_path):
    """§ Validation, "Weights are usable", the zero half: a weight is what a
    unit stands for, and a unit
    standing for nothing is a unit that should not be in the roster."""
    _weighted_table(tmp_path, "p1,2.0\np2,0\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
                "weight_by": "sampling_weight",
            }
        }
    )
    assert "E-DATA-WEIGHT-INVALID" in codes(path)


def test_a_negative_weight_is_refused(write_config, tmp_path):
    """§ Validation, "Weights are usable", the negative half. Separate from the
    zero case on purpose: a
    check written `< 0` passes the negative test and lets a zero weight through."""
    _weighted_table(tmp_path, "p1,2.0\np2,-1.5\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
                "weight_by": "sampling_weight",
            }
        }
    )
    assert "E-DATA-WEIGHT-INVALID" in codes(path)


def test_a_non_numeric_weight_is_refused(write_config, tmp_path):
    """A weight that is not a number cannot be one. `csv.DictReader` yields
    strings for every column, so "numeric" here means `is_measurement_numeric`
    — the single authority — and not `isinstance(v, (int, float))`, which no
    table-sourced value ever satisfies."""
    _weighted_table(tmp_path, "p1,2.0\np2,unknown\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
                "weight_by": "sampling_weight",
            }
        }
    )
    assert "E-DATA-WEIGHT-INVALID" in codes(path)


def test_a_non_finite_weight_is_refused(write_config, tmp_path):
    """`float("nan")` parses, and `nan <= 0` is `False`, so a positivity test
    alone admits it — and every weighted mean it touches is `nan`."""
    _weighted_table(tmp_path, "p1,2.0\np2,nan\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
                "weight_by": "sampling_weight",
            }
        }
    )
    assert "E-DATA-WEIGHT-INVALID" in codes(path)


def test_the_value_check_is_skipped_without_a_roster(write_config):
    """The reachable half of the skip: with no roster there are no values, and
    the name check above still reports. Called directly so the two halves are
    distinguishable rather than inferred from one `validate_config` run."""
    c = Collector()
    _check_weight_by(
        {"attributes": ["sampling_weight"], "weight_by": "sampling_weight"}, None, c
    )
    assert not c.findings


@pytest.mark.parametrize("unset", [{}, {"weight_by": None}])
def test_a_weight_looking_column_warns_when_nothing_declares_it(write_config, tmp_path, unset):
    """§ Validation, "Weighting looks undeclared". The positive direction comes
    first: a warning that can never fire
    passes its own negative test trivially.

    Both forms of "unset" are run. `init` materializes `weight_by: null`, so the
    explicit null is the shape a real config carries and a check keyed on the
    key's *absence* would miss it entirely. The message is asserted too: "a
    warning fired" and "the warning about this column fired" are different
    claims, and only the second is what row 293 promises."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
                **unset,
            }
        }
    )
    found = messages_by_code(path)
    assert "W-DATA-WEIGHT-UNDECLARED" in found
    assert "sampling_weight" in found["W-DATA-WEIGHT-UNDECLARED"]


def test_no_weight_warning_for_a_constant_column(write_config, tmp_path):
    """A column that does not vary is not a sampling weight, and warning about it
    would train a reader to ignore the warning."""
    _weighted_table(tmp_path, "p1,2.0\np2,2.0\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
            }
        }
    )
    assert "W-DATA-WEIGHT-UNDECLARED" not in codes(path)


def test_no_weight_warning_for_a_column_the_name_test_does_not_match(write_config, tmp_path):
    """The name test is what keeps this warning off `age`, `dose` and `latency`,
    every one of which is numeric, positive and varying. Same fixture as the
    positive case but for the column name, so the two pin the trigger between
    them."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n", column="dose")
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["dose"]}}
    )
    assert "W-DATA-WEIGHT-UNDECLARED" not in codes(path)


def test_no_weight_warning_once_weight_by_declares_the_column(write_config, tmp_path):
    """The warning is about a weight going *unused*, so declaring it is what
    silences it — the one thing the message tells a reader to do."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
                "weight_by": "sampling_weight",
            }
        }
    )
    assert "W-DATA-WEIGHT-UNDECLARED" not in codes(path)


def test_no_weight_warning_for_a_zero_valued_weight_looking_column(write_config, tmp_path):
    """`0` is not a positive weight, so the column does not look like an inverse
    sampling probability — and with nothing declaring it, there is no
    `E-DATA-WEIGHT-INVALID` to report either. Silence is the right answer for a
    column the design never claimed was a weight."""
    _weighted_table(tmp_path, "p1,2.0\np2,0\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
            }
        }
    )
    found = codes(path)
    assert "W-DATA-WEIGHT-UNDECLARED" not in found
    assert "E-DATA-WEIGHT-INVALID" not in found


# --- a weighted design beside a contrast ------------------------------------
#
# `E-DATA-WEIGHT-UNSUPPORTED` is retired: `weight_by` is a declaration core
# honors, for a single condition's value, interval and `n.effective`. No
# *contrast* construction weights — `paired_t_over_units` takes differences and
# nothing else — so the one combination that would publish a wrong delta is
# refused under its own code until the paired estimators weight.


def _weighted_units(**extra) -> dict:
    """The `data.units` block these checks share: a declared weight that resolves
    and passes every value check, so the only finding left is the one under test."""
    return {
        "from": "index.csv",
        "key": "patient_id",
        "attributes": ["sampling_weight"],
        "weight_by": "sampling_weight",
        **extra,
    }


def test_a_declared_weight_by_is_no_longer_refused(write_config, tmp_path):
    """The retirement itself. A weighted roster with no contrast in it validates
    clean — not merely free of the old code, but free of every finding, which is
    what says the design is one core runs today."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config({"data.units": _weighted_units()})
    assert codes(path) == set()


def test_a_weighted_generated_comparison_is_refused(write_config, tmp_path):
    """A baseline over an enumerated axis generates two `vs_baseline` deltas, and
    `paired_t_over_units` weights neither side. The delta and its interval would
    be unweighted numbers reported beside weighted per-condition values — two
    answers to different questions in one block."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": _weighted_units(),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall"]},
            },
        }
    )
    assert codes(path) == {"E-DATA-WEIGHT-CONTRAST"}
    message = messages_by_code(path)["E-DATA-WEIGHT-CONTRAST"]
    assert "publishes 2 comparisons," in message


def test_a_weighted_declared_contrast_is_refused(write_config, tmp_path):
    """The other source of a comparison. A `statistics.contrasts` entry is named
    rather than generated, so no baseline is involved at all — and it reaches the
    same unweighted `paired_t_over_units`, which is why the guard reads the
    resolved family rather than `sweep.baseline`."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": _weighted_units(),
            "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}},
            "statistics": {
                "contrasts": [
                    {
                        "id": "spearman_vs_pearson",
                        "of": "method=spearman",
                        "against": "method=pearson",
                    }
                ]
            },
        }
    )
    assert codes(path) == {"E-DATA-WEIGHT-CONTRAST"}
    # The singular, and pinned as a whole word: `"1 comparison" in ...` would
    # pass against `1 comparisons` too, which is the shape this slice keeps
    # writing tests that cannot see.
    message = messages_by_code(path)["E-DATA-WEIGHT-CONTRAST"]
    assert "publishes 1 comparison," in message


def test_a_weighted_baseline_that_generates_no_comparison_stays_legal(write_config, tmp_path):
    """The edge that makes the guard narrower than `sweep.baseline` being
    declared. A baseline with no axis beside it expands to one condition, which
    `resolve_contrasts` skips as an `of` — the run publishes no delta at all, so
    there is no unweighted number for the refusal to prevent. Refusing it would
    strand a design core computes correctly."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    overrides = {
        "data.units": _weighted_units(),
        "sweep": {"baseline": {"analysis.method": "pearson"}},
    }
    assert codes(write_config(overrides)) == set()
    # The control that must report: the same weighted config with one axis added
    # generates a comparison and is refused, so the silence above is this
    # baseline's shape rather than a guard that never fires.
    crossed = dict(overrides)
    crossed["sweep"] = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]},
    }
    assert codes(write_config(crossed)) == {"E-DATA-WEIGHT-CONTRAST"}


def test_an_unweighted_comparison_is_untouched(write_config, tmp_path):
    """The neighbouring shape: the same sweep with no `weight_by` is the ordinary
    design, and nothing about it moved."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["sampling_weight"],
            },
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall"]},
            },
        }
    )
    assert "E-DATA-WEIGHT-CONTRAST" not in codes(path)


def test_a_weighted_report_by_is_not_a_contrast(write_config, tmp_path):
    """`statistics.report_by` repeats a metric over strata "without adding
    executions or joining the correction family" — it publishes no delta, so it
    is not a contrast and the refusal must not reach it. A subgroup someone wants
    to *test* is a `within` contrast, which does join the family and is refused
    above."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,sampling_weight,cohort\np1,2.0,a\np2,3.0,b\n"
    )
    path = write_config(
        {
            "data.units": _weighted_units(attributes=["sampling_weight", "cohort"]),
            "statistics": {"report_by": ["cohort"]},
        }
    )
    assert codes(path) == set()


# --- a clustered design -----------------------------------------------------
#
# `_check_unimplemented` refused a truthy `data.units.cluster_by` outright when
# these were written, so a declaration check reported beside that refusal and a
# test asserting only "some finding fired" would have passed off the refusal
# instead. H3b task 12 retired it, the declaration now changing the record. What
# survives from that arrangement is worth keeping on its own terms: every check
# below is also exercised by a direct call, where no config-level finding can
# stand in for the one under test.


def _clustered_table(tmp_path: Path, header: str, body: str) -> None:
    """Write the roster these checks read, into the directory `write_config`
    points `data.input_dir` at. `write_config` writes a `patient_id`-only
    `index.csv`, so a test needing more columns overwrites it here — writing it
    anywhere else is how a probe comes back empty for every input."""
    (tmp_path / "input" / "index.csv").write_text(f"{header}\n{body}")


_SITE_BODY = "".join(f"p{i},{s}\n" for i, s in enumerate("aaabbbcccddd"))


def test_a_cluster_by_naming_no_attribute_is_reported(write_config, tmp_path):
    """§ Validation, "Cluster attribute exists": `cluster_by` names `site`, which
    is not a unit attribute. `data.units.attributes` is the reference set — a
    cluster is read per unit when the split is drawn, so it has to survive
    resolution — and that is the opposite side of the line from
    `measurements.by`, which names a source column."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "cluster_by": "site"}}
    )
    assert "E-DATA-CLUSTER-UNKNOWN" in codes(path)


def test_a_declared_cluster_attribute_is_not_reported_unknown(write_config, tmp_path):
    """The other half of the same declaration: declaring the attribute is what
    makes the name check pass, so it discriminates rather than reporting on every
    `cluster_by` there is."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site"],
                "cluster_by": "site",
            }
        }
    )
    assert "E-DATA-CLUSTER-UNKNOWN" not in codes(path)


def test_an_empty_cluster_by_is_reported(write_config, tmp_path):
    """An empty declaration changes no behavior, which is the failure a truthy
    read of it would hide — and `_check_unimplemented`'s refusal, which is such a
    read, stays silent on it, so this is the only finding it draws."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site"],
                "cluster_by": "",
            }
        }
    )
    # The whole finding set: an empty `cluster_by` draws the name check and nothing
    # else. Asserted exactly since task 12 retired the unbuilt-declaration refusal
    # that used to be the reason for naming a second code here.
    assert codes(path) == {"E-DATA-CLUSTER-UNKNOWN"}


def test_a_cluster_by_under_a_glob_source_is_reported(write_config, tmp_path):
    """The glob cross-check, and it costs nothing extra: a glob yields a key and
    a path and nothing else, so `_from_glob` refuses every declared attribute and
    a `cluster_by` there can never name one."""
    (tmp_path / "input" / "a.dcm").write_bytes(b"\x00")
    path = write_config(
        {"data.units": {"from": {"glob": "*.dcm"}, "key": "path", "cluster_by": "site"}}
    )
    assert "E-DATA-CLUSTER-UNKNOWN" in codes(path)


def test_the_cluster_name_check_reports_without_a_roster():
    """Called directly, with no roster and no `validate_config` around it: the name
    half is checked from the declaration alone, so it reports whether or not a
    roster resolved — which is the property this pins, and the reason it survived
    the retirement of the refusal it used to be contrasted against."""
    c = Collector()
    _check_cluster_by({}, {"attributes": ["age"], "cluster_by": "site"}, None, c)
    assert [f.code for f in c.findings] == ["E-DATA-CLUSTER-UNKNOWN"]


def test_a_non_string_cluster_by_is_left_to_the_envelope(write_config, tmp_path):
    """`E-CONFIG-TYPE` owns it, and describing `3` as "empty" would fit neither
    the value nor the remedy.

    Both halves are asserted, and the second is why this is not a vacuous test:
    silence here proves the check defers, and `E-CONFIG-TYPE` in `codes` proves
    there is something to defer *to* — `envelope.py`'s `LEAF_TYPES` really does
    type `data.units.cluster_by` a `str`. Without the second assertion this could
    not tell "correctly deferred" from "silently dropped" — a distinction that used
    to be masked by the unbuilt-declaration refusal firing on a truthy `3`, and
    which task 12's retirement of that refusal is what makes load-bearing."""
    c = Collector()
    _check_cluster_by({}, {"attributes": ["site"], "cluster_by": 3}, None, c)
    assert not c.findings
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site"],
                "cluster_by": 3,
            }
        }
    )
    assert "E-CONFIG-TYPE" in codes(path)


# --- the clustered contrast family, which does not exist ----------------------
#
# H3b task 12 minted `E-DATA-CLUSTER-CONTRAST` in the place H3a's
# `E-DATA-WEIGHT-CONTRAST` and H2's `E-SWEEP-SAMPLE-BASELINE` occupy: a narrow
# refusal of a *combination* that retiring a broad declaration refusal had just
# made reachable. § Statistical reporting gives each contrast construction a
# `_clustered` suffix under `cluster_by` — cluster-robust *t* forms and percentile
# forms resampling whole clusters "jointly across both sides when paired" — and
# none of those five exists. The probes below mirror the weighted set above one for
# one, because the guard is deliberately the same shape: it reads the *resolved*
# comparison family, not the declaration.


def _clustered_units(**extra) -> dict:
    """The `data.units` block these checks share, the shape `_weighted_units` above
    has: a declared cluster that resolves and passes every value check, so the only
    finding left is the one under test."""
    return {
        "from": "index.csv",
        "key": "patient_id",
        "attributes": ["site"],
        "cluster_by": "site",
        **extra,
    }


def test_a_declared_cluster_by_is_no_longer_refused(write_config, tmp_path):
    """The retirement itself. A clustered roster with no contrast in it validates
    clean — not merely free of the old code, but free of every finding, which is
    what says the design is one core runs today."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    assert codes(write_config({"data.units": _clustered_units()})) == set()


def test_a_clustered_generated_comparison_is_refused(write_config, tmp_path):
    """A baseline over an enumerated axis generates two `vs_baseline` deltas, and
    `paired_t_over_units` takes a list of per-unit differences and nothing else —
    no membership, so no cluster. The delta and its interval would be drawn as if
    every unit were independent, beside per-condition intervals that are
    cluster-robust, with nothing in the record saying which is which."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": _clustered_units(),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall"]},
            },
        }
    )
    assert codes(path) == {"E-DATA-CLUSTER-CONTRAST"}
    assert "publishes 2 comparisons," in messages_by_code(path)["E-DATA-CLUSTER-CONTRAST"]


def test_a_clustered_declared_contrast_is_refused(write_config, tmp_path):
    """The other source of a comparison. A `statistics.contrasts` entry is named
    rather than generated, so no baseline is involved at all — and it reaches the
    same unclustered estimator, which is why the guard reads the resolved family
    rather than `sweep.baseline`."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": _clustered_units(),
            "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}},
            "statistics": {
                "contrasts": [
                    {
                        "id": "spearman_vs_pearson",
                        "of": "method=spearman",
                        "against": "method=pearson",
                    }
                ]
            },
        }
    )
    assert codes(path) == {"E-DATA-CLUSTER-CONTRAST"}
    # The singular, pinned as a whole word: `"1 comparison" in ...` would pass
    # against `1 comparisons` too.
    assert "publishes 1 comparison," in messages_by_code(path)["E-DATA-CLUSTER-CONTRAST"]


def test_a_clustered_baseline_that_generates_no_comparison_stays_legal(write_config, tmp_path):
    """The edge that makes the guard narrower than `sweep.baseline` being declared,
    and the one H3a's implementer found. A baseline with no axis beside it expands
    to one condition, which `resolve_contrasts` skips as an `of` — the run publishes
    no delta, so there is no too-narrow interval for the refusal to prevent."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    overrides = {
        "data.units": _clustered_units(),
        "sweep": {"baseline": {"analysis.method": "pearson"}},
    }
    assert codes(write_config(overrides)) == set()
    # The control that must report: the same clustered config with one axis added
    # generates a comparison and is refused, so the silence above is this
    # baseline's shape rather than a guard that never fires.
    crossed = dict(overrides)
    crossed["sweep"] = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]},
    }
    assert codes(write_config(crossed)) == {"E-DATA-CLUSTER-CONTRAST"}


def test_an_unclustered_comparison_is_untouched(write_config, tmp_path):
    """The neighbouring shape: the same sweep with no `cluster_by` is the ordinary
    design, and nothing about it moved."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["site"]},
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall"]},
            },
        }
    )
    assert "E-DATA-CLUSTER-CONTRAST" not in codes(path)


def test_a_clustered_report_by_is_not_a_contrast(write_config, tmp_path):
    """`statistics.report_by` repeats a metric over strata "without adding
    executions or joining the correction family" — it publishes no delta, and the
    per-condition aggregation it repeats *is* clustered, so the refusal must not
    reach it. A subgroup someone wants to *test* is a `within` contrast, which does
    join the family and is refused above."""
    body = "".join(f"p{i},s{i % 4},a\n" for i in range(12))
    _clustered_table(tmp_path, "patient_id,site,cohort", body)
    path = write_config(
        {
            "data.units": _clustered_units(attributes=["site", "cohort"]),
            "statistics": {"report_by": ["cohort"]},
        }
    )
    assert codes(path) == set()


def test_an_empty_cluster_by_beside_a_comparison_is_not_the_contrast_refusal(
    write_config, tmp_path
):
    """The under-firing control on the other side: an empty `cluster_by` declares
    no clustering, so nothing about the delta is wrong and only the name check
    reports. A truthy read is what keeps the two apart."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": _clustered_units(cluster_by=""),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman"]},
            },
        }
    )
    assert codes(path) == {"E-DATA-CLUSTER-UNKNOWN"}


def test_a_parameter_named_stratify_by_does_not_silence_the_cluster_warning(
    write_config, tmp_path
):
    """The exclusion walk covers the four blocks that describe the design, not
    `parameters` — a template may declare a parameter of any name, and one called
    `stratify_by` silencing a real cluster column would be invisible to a reader."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["site"]},
            "parameters.analysis": {
                "method": "pearson",
                "min_samples": 30,
                "confidence": 0.95,
                "drop_missing": True,
                "stratify_by": "site",
            },
        }
    )
    assert "W-DATA-CLUSTER-UNDECLARED" in codes(path)


@pytest.mark.parametrize("unset", [{}, {"cluster_by": None}])
def test_a_cluster_looking_column_warns_when_nothing_declares_it(write_config, tmp_path, unset):
    """§ Validation, "Clustering looks undeclared". The positive direction comes
    first: a warning that can never fire passes its own negative test trivially.

    Both forms of "unset" are run — `init` materializes `cluster_by: null`, so a
    check keyed on the key's absence would miss the shape a real config carries.
    Four sites over twelve units: repeated, non-numeric, more than two, and every
    unit carries one."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site"],
                **unset,
            }
        }
    )
    found = messages_by_code(path)
    assert "W-DATA-CLUSTER-UNDECLARED" in found
    assert "site" in found["W-DATA-CLUSTER-UNDECLARED"]


def test_the_worked_examples_own_attributes_do_not_warn(write_config, tmp_path):
    """The control that decides whether the trigger is usable at all. `cohort-pilot`
    declares `[label, age, sex]` and no `cluster_by`, and `sex` has two values over
    many units — which "few distinct values, many units each" reads as a cluster.
    A warning that fires on the project's own worked example is one every user
    learns to ignore.

    Each attribute is silenced by a different clause, which is what makes this a
    test of the trigger rather than of one clause: `age` by the type clause, `label`
    and `sex` by the "more than two distinct values" clause."""
    _clustered_table(
        tmp_path,
        "patient_id,label,age,sex",
        "".join(
            f"p{i},{'case' if i % 2 else 'control'},{30 + (i % 4) * 5},{'f' if i % 3 else 'm'}\n"
            for i in range(12)
        ),
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["label", "age", "sex"],
            }
        }
    )
    assert "W-DATA-CLUSTER-UNDECLARED" not in codes(path)


def test_no_cluster_warning_for_a_numeric_column(write_config, tmp_path):
    """The type clause. `age`, `dose` and `latency` have repeated values too, and
    a numeric column with repeated values is a measurement far more often than an
    identifier — the cost being a missed integer-coded id, which is the right way
    to be wrong here. Same fixture as the positive case but for the values."""
    _clustered_table(
        tmp_path,
        "patient_id,site",
        "".join(f"p{i},{s}\n" for i, s in enumerate("111222333444")),
    )
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["site"]}}
    )
    assert "W-DATA-CLUSTER-UNDECLARED" not in codes(path)


def test_no_cluster_warning_for_a_column_that_is_a_second_key(write_config, tmp_path):
    """The "held by more than one unit" clause: a column with one value per unit
    is a second identity, not a grain units share."""
    _clustered_table(
        tmp_path,
        "patient_id,site",
        "".join(f"p{i},s{i}\n" for i in range(12)),
    )
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["site"]}}
    )
    assert "W-DATA-CLUSTER-UNDECLARED" not in codes(path)


def test_no_cluster_warning_for_a_column_with_a_blank_cell(write_config, tmp_path):
    """"Every unit carries a value for it" reads an empty cell as no value. A
    sparse column would otherwise satisfy the type and repetition clauses on its
    blanks alone."""
    _clustered_table(
        tmp_path,
        "patient_id,site",
        "".join(f"p{i},{s}\n" for i, s in enumerate(["a", "a", "b", "b", "c", ""])),
    )
    path = write_config(
        {"data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["site"]}}
    )
    assert "W-DATA-CLUSTER-UNDECLARED" not in codes(path)


def test_no_cluster_warning_once_cluster_by_declares_the_column(write_config, tmp_path):
    """The warning is about a cluster going *undeclared*, so declaring it is what
    silences it — the one thing the message tells a reader to do."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site"],
                "cluster_by": "site",
            }
        }
    )
    assert "W-DATA-CLUSTER-UNDECLARED" not in codes(path)


def test_no_cluster_warning_for_an_attribute_null_test_shuffles(write_config, tmp_path):
    """One of the exclusions: a cluster is what shuffling *respects*, not what it
    names. Reported through `validate_config` even though `statistics.null_test`
    is itself refused in this build — the refusal is a finding beside this one,
    not a substitute for it."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["site"]},
            "statistics": {"null_test": {"method": "permutation", "n": 10, "shuffle": "site"}},
        }
    )
    found = codes(path)
    assert "W-DATA-CLUSTER-UNDECLARED" not in found
    assert "E-STATS-NULLTEST-UNSUPPORTED" in found


def test_no_cluster_warning_for_an_attribute_something_stratifies_on(write_config, tmp_path):
    """`stratify_by` must be constant within a cluster, so it is coarser than one.
    Collected by walking the document for the key, so a `stratify_by` on any block
    accounts for its attribute — here a `fold` repeat level's."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": {"from": "index.csv", "key": "patient_id", "attributes": ["site"]},
            "replication.repeats": [{"kind": "fold", "k": 2, "stratify_by": "site"}],
        }
    )
    assert "W-DATA-CLUSTER-UNDECLARED" not in codes(path)


def test_the_cluster_warning_is_skipped_without_a_roster():
    """The reachable half of the skip: with no roster there is no column to look
    at. Called directly, so it is distinguishable from a run where every clause
    simply failed."""
    c = Collector()
    _check_cluster_by({}, {"attributes": ["site"]}, None, c)
    assert not c.findings


# --- a contrast whose two sides differ on a group axis has no unpaired ------
# construction ----------------------------------------------------------------
#
# `E-DATA-ALLOCATION-CONTRAST` is the third row in this family, beside
# `E-DATA-WEIGHT-CONTRAST` and `E-DATA-CLUSTER-CONTRAST` above — a refusal of a
# *combination* a resolved comparison family can carry, not of a declaration.
# It differs from its two siblings in the one way that matters: those two fire
# on `comparisons > 0`, because a weight or a cluster affects every contrast in
# the family alike. This one cannot — a `groups × grid` design's within-arm
# comparisons (control-pearson vs. control-spearman) are paired and computable,
# sharing the same arm's units, while its cross-arm ones (control-pearson vs.
# treatment-pearson) are not, so the guard has to read each resolved comparison
# on its own rather than the family's size.


def test_a_group_axis_with_no_comparison_is_untouched(write_config):
    """The first control: a declared `groups` axis with no baseline and no
    `statistics.contrasts` resolves no comparison at all — `resolve_contrasts`
    returns nothing to compare, so there is no unpaired delta for this guard to
    prevent and it must draw nothing new. This is the plain groups-axis config
    already exercised elsewhere in this file (`E-DATA-ALLOCATION-WITHIN-ARMS`,
    since no `allocation` is declared beside the axis), and its finding set is
    the exact one it has today — asserted here as a whole set, not a
    membership check, so a change that adds `E-DATA-ALLOCATION-CONTRAST` to it
    would be caught."""
    axis = [{"by": "arm", "levels": ["control", "treatment"]}]
    assert codes(write_config({"sweep": {"groups": axis}})) == {
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }


def test_a_within_allocation_contrast_is_untouched(write_config):
    """The second control: an ordinary parameter sweep with a baseline — no
    `groups` axis anywhere, so every condition's `selectors` is empty and the
    guard's intersection is always empty. Its contrast is genuinely paired
    (`reference.md` § Allocation: parameter axes only, under `within` or
    `between`, share the same arm's units), and the finding set is empty,
    exactly as it is without this task's change."""
    path = write_config(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall"]},
            }
        }
    )
    assert codes(path) == set()


def test_a_generated_cross_arm_comparison_is_refused_and_the_within_arm_one_is_not(
    write_config,
):
    """The third control, and the one the guard exists for: a `groups × grid`
    design whose baseline fixes the group axis to one arm (`control`) rather
    than per-cell. That baseline is itself refused (`E-SWEEP-BASELINE-GROUP`),
    and deliberately so — it is the *only* declaration that makes a generated
    `vs_baseline` cross arms, since every other baseline expands over the group
    axis and targets each condition's own cell. `validate` collects rather than
    stops, so the per-comparison guard still runs here and is what this test
    reads; the route that carries this code alone is the declared contrast in
    the test below. `sweep.expand` then renders one baseline row and
    `contrasts.resolve_contrasts` compares every other condition against it —
    including the `treatment` ones, which is what makes the baseline-generated
    route (not just a declared `statistics.contrasts` entry) produce a
    cross-arm comparison.

    Four conditions result: `control/spearman` and `control/kendall`, each
    differing from the `control/pearson` baseline on `analysis.method` alone
    (same arm, paired, untouched), and `treatment/spearman` and
    `treatment/kendall`, each differing on `arm` too (cross-arm, disjoint
    units, refused). The count discriminates the guard from a
    `comparisons > 0` one: four resolved comparisons, and the code fires on
    exactly the two that actually cross arms — not zero, and not four."""
    path = write_config(
        {
            "sweep": {
                "groups": [{"by": "arm", "levels": ["control", "treatment"]}],
                "grid": {"analysis.method": ["spearman", "kendall"]},
                "baseline": {"arm": "control", "analysis.method": "pearson"},
            }
        }
    )
    c = Collector()
    validate_config(path, c)
    found = [f for f in c.findings if f.code == "E-DATA-ALLOCATION-CONTRAST"]
    assert len(found) == 2
    named = {f.message for f in found}
    assert any("'arm=treatment__method=spearman'" in m for m in named)
    assert any("'arm=treatment__method=kendall'" in m for m in named)
    # Neither within-arm comparison is named by any finding.
    assert not any("'arm=control__method=spearman'" in m for m in named)
    assert not any("'arm=control__method=kendall'" in m for m in named)
    for message in named:
        assert "differ on group axis arm" in message


def test_a_declared_contrast_across_arms_is_refused(write_config):
    """The other source of a comparison: a `statistics.contrasts` entry naming
    two conditions on either side of a `groups` axis directly, with no baseline
    involved at all. This is the declared-contrast branch the generated one
    above does not exercise — `resolve_contrasts` reaches it through the
    `statistics.contrasts` loop rather than through a baseline match, so a
    mutation that only breaks the baseline-generated path would still fail
    this test."""
    axis = [{"by": "arm", "levels": ["control", "treatment"]}]
    path = write_config(
        {
            "sweep": {"groups": axis},
            "statistics": {
                "contrasts": [
                    {"id": "t_vs_c", "of": "arm=treatment", "against": "arm=control"}
                ]
            },
        }
    )
    c = Collector()
    validate_config(path, c)
    found = [f for f in c.findings if f.code == "E-DATA-ALLOCATION-CONTRAST"]
    assert len(found) == 1
    assert "'arm=treatment'" in found[0].message
    assert "'arm=control'" in found[0].message
    assert "differ on group axis arm" in found[0].message


# --- `groups × cluster_by` — task 19 Step 3 ------------------------------------
#
# No earlier task combined a declared `groups` axis with a declared `cluster_by`.
# The fixture below is built so the two partitions genuinely cross — a reader
# has to be able to check the discrimination without running anything, per the
# addendum — and it deliberately carries no `statistics.contrasts` and no
# `sweep.baseline` beside the axis: the addendum's own correction to this
# task's brief, because a natural `baseline: {arm: control}` here would publish
# a cross-arm comparison and draw `E-DATA-CLUSTER-CONTRAST` *and*
# `E-DATA-ALLOCATION-CONTRAST` instead of validating — a config this test is
# not about.

_GROUPS_CLUSTER_ARMS = {
    "control": ["c0", "c1", "c2", "c3", "c4", "c5", "c6"],
    "treatment": ["t0", "t1", "t2", "t3", "t4"],
}
# Sites `A` and `B` span both arms (A: c0,c1,t0; B: c2,c3,t1,t2), and `control`
# alone touches three distinct sites — the crossing task 12's own 7/5 arm
# fixture and `test_runner.py`'s 5-unit/3-cluster harness do NOT have, since
# neither carries the other's partitioning attribute at all. `by_attribute`
# reads the arm rather than drawing it (§ Clustered units), and a cluster
# spanning two arms is documented as correct under that method — this fixture
# is not the matched case-control design that requires it, but it is legal
# under it, which is what this test is checking is still true.
#
# `C` and `D` are arm-exclusive (`C` only in `control`, `D` only in
# `treatment`) — kept in sync with `tests/test_cli.py`'s identical mapping,
# whose own end-to-end execution test needed at least one arm-exclusive site
# on each side to discriminate a whole-roster cluster count from either arm's
# own (review found the first, all-crossing draft could not: every site being
# shared made both arms' correct count and the whole roster's coincide at 3).
# This validate-level test's own assertions are declaration-level only
# (`_check_cluster_by` reads `attributes`, not per-unit values), so the change
# does not affect what it checks — kept in sync purely so the "same design"
# claim stays true rather than because this test needs the discrimination.
_GROUPS_CLUSTER_SITES = {
    "c0": "A", "c1": "A", "c2": "B", "c3": "B", "c4": "C", "c5": "C", "c6": "C",
    "t0": "A", "t1": "B", "t2": "B", "t3": "D", "t4": "D",
}


def _groups_cluster_csv() -> str:
    rows = ["patient_id,arm,site"]
    for arm, keys in _GROUPS_CLUSTER_ARMS.items():
        for key in keys:
            rows.append(f"{key},{arm},{_GROUPS_CLUSTER_SITES[key]}")
    return "\n".join(rows) + "\n"


def _groups_cluster_doc(**extra) -> dict:
    doc = {
        "data.units": {
            "from": "index.csv",
            "key": "patient_id",
            "attributes": ["arm", "site"],
            "cluster_by": "site",
            "allocation": "between",
            "assign": {"arm": {"method": "by_attribute"}},
        },
        "sweep": {"groups": [{"by": "arm", "levels": ["control", "treatment"]}]},
    }
    doc.update(extra)
    return doc


def test_groups_and_cluster_by_compose_with_no_comparison(write_config, tmp_path):
    """The combination itself, with no baseline and no `statistics.contrasts`: a
    real `between` + `by_attribute` + `cluster_by` config over a roster whose
    arms and clusters genuinely cross, validating fully clean. This is what
    proves the combination itself is not what either refusal in this file
    reads — only a comparison beside it is, checked by the two controls below."""
    (tmp_path / "input" / "index.csv").write_text(_groups_cluster_csv())
    assert _error_codes(write_config(_groups_cluster_doc())) == set()


def test_a_contrast_beside_groups_and_cluster_by_draws_both_refusals(write_config, tmp_path):
    """The can-fail control for the clean composition above: adding a declared
    `statistics.contrasts` entry across the two arms to the SAME fixture must
    draw both `E-DATA-CLUSTER-CONTRAST` (task 12 — no clustered contrast
    construction exists) and `E-DATA-ALLOCATION-CONTRAST` (task 16b — the two
    sides are disjoint arms), asserted as the exact set. After task 16b there
    are two reporters over one comparison, not one, and this is checked rather
    than assumed."""
    (tmp_path / "input" / "index.csv").write_text(_groups_cluster_csv())
    doc = _groups_cluster_doc(
        statistics={
            "contrasts": [
                {"id": "t_vs_c", "of": "arm=treatment", "against": "arm=control"}
            ]
        }
    )
    assert _error_codes(write_config(doc)) == {
        "E-DATA-CLUSTER-CONTRAST",
        "E-DATA-ALLOCATION-CONTRAST",
    }


# --- a cluster and a weight must not vary within a unit's measurement rows ----
#
# `units.collapse_measurements` raises; `_check_units` wraps `resolve_units` in
# `except ContractError`, which is the route `E-UNITS-COLLAPSE-RULE` and
# `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` already take to become findings. These
# tests are the validate surface of that route — the unit-level tests in
# `test_units.py` pin the raise itself.

_MEASURED_UNITS = {
    "from": "index.csv",
    "key": "patient_id",
    "attributes": ["read_id", "site", "sampling_weight"],
    "measurements": {"by": "read_id", "collapse": "first"},
}


def test_a_cluster_varying_within_a_units_rows_is_reported(write_config, tmp_path):
    """§ Clustered units: replicate rows declaring `S1` and `S2` would collapse to
    whichever the file happens to list first, and the unit's real site would then
    be on both sides of a split."""
    _clustered_table(
        tmp_path,
        "patient_id,read_id,site,sampling_weight",
        "p1,r1,S1,2\np1,r2,S2,2\np2,r3,S3,2\n",
    )
    path = write_config({"data.units": dict(_MEASURED_UNITS, cluster_by="site")})
    assert "E-DATA-CLUSTER-VARIES" in codes(path)


def test_agreeing_cluster_rows_are_not_reported(write_config, tmp_path):
    """The cluster half's control: the same config over rows that agree. A check
    that reported for every measured roster would pass the test above too."""
    _clustered_table(
        tmp_path,
        "patient_id,read_id,site,sampling_weight",
        "p1,r1,S1,2\np1,r2,S1,2\np2,r3,S3,2\n",
    )
    path = write_config({"data.units": dict(_MEASURED_UNITS, cluster_by="site")})
    found = codes(path)
    assert "E-DATA-CLUSTER-VARIES" not in found
    assert "E-DATA-WEIGHT-VARIES" not in found


def test_a_weight_varying_within_a_units_rows_is_reported(write_config, tmp_path):
    """The gap H3a left: § Weighted samples states this rule, and until now
    nothing checked it. Reported at `validate`, through the same route."""
    _clustered_table(
        tmp_path,
        "patient_id,read_id,site,sampling_weight",
        "p1,r1,S1,1\np1,r2,S1,99\np2,r3,S3,2\n",
    )
    path = write_config({"data.units": dict(_MEASURED_UNITS, weight_by="sampling_weight")})
    assert "E-DATA-WEIGHT-VARIES" in codes(path)


def test_agreeing_weight_rows_are_not_reported(write_config, tmp_path):
    """The weight half's own control."""
    _clustered_table(
        tmp_path,
        "patient_id,read_id,site,sampling_weight",
        "p1,r1,S1,2\np1,r2,S1,2\np2,r3,S3,2\n",
    )
    path = write_config({"data.units": dict(_MEASURED_UNITS, weight_by="sampling_weight")})
    assert "E-DATA-WEIGHT-VARIES" not in codes(path)


def test_neither_check_fires_where_measurements_is_undeclared(write_config, tmp_path):
    """The worked example declares neither `measurements` nor `cluster_by`, and
    every roster with one row per unit is in this shape: nothing merges, so no
    column can disagree with itself and neither code may appear."""
    _clustered_table(
        tmp_path,
        "patient_id,site,sampling_weight",
        "p1,S1,2\np2,S3,2\n",
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["site", "sampling_weight"],
                "cluster_by": "site",
                "weight_by": "sampling_weight",
            }
        }
    )
    found = codes(path)
    assert "E-DATA-CLUSTER-VARIES" not in found
    assert "E-DATA-WEIGHT-VARIES" not in found


def test_validate_reports_rather_than_raising_on_a_varying_cluster(write_config, tmp_path):
    """`validate` collects findings and never raises. The `except ContractError`
    in `_check_units` is what makes that true of this raise too, and a test
    calling `validate_config` directly is what proves nothing escaped."""
    _clustered_table(
        tmp_path,
        "patient_id,read_id,site,sampling_weight",
        "p1,r1,S1,2\np1,r2,S2,2\n",
    )
    path = write_config({"data.units": dict(_MEASURED_UNITS, cluster_by="site")})
    c = Collector()
    validate_config(path, c)
    assert any(f.code == "E-DATA-CLUSTER-VARIES" for f in c.findings)


# --- an arm must not vary within a unit's measurement rows --------------------
#
# The same route as the cluster/weight pair above — `units.collapse_measurements`
# raises, `_check_units` catches under `except ContractError` — for the third
# declaration `CONSTANT_COLUMN_RULES` now reaches: `assign.<axis>.from`. No
# fixture below declares `cluster_by`, so a varying `arm` cannot be mistaken for
# a varying cluster.

_ARM_MEASURED_UNITS = {
    "from": "index.csv",
    "key": "patient_id",
    "attributes": ["read_id", "arm"],
    "assign": {"arm": {"method": "by_attribute"}},
    "measurements": {"by": "read_id", "collapse": "first"},
}


def test_an_arm_varying_within_a_units_rows_is_reported(write_config, tmp_path):
    """§ Validation's *Arm is constant within a unit*: replicate rows declaring
    `control` and `treatment` would collapse to whichever the file lists
    first — deciding which condition p1 is measured in, not merely which side
    of a split it lands on."""
    _clustered_table(
        tmp_path,
        "patient_id,read_id,arm",
        "p1,r1,control\np1,r2,treatment\np2,r3,control\n",
    )
    path = write_config({"data.units": _ARM_MEASURED_UNITS})
    assert "E-DATA-ASSIGN-VARIES" in codes(path)


def test_agreeing_arm_rows_are_not_reported(write_config, tmp_path):
    """The arm half's own control. Same shape, rows that agree — must not
    report — and the config declares `assign` at all, so a check that never
    ran would also pass this."""
    _clustered_table(
        tmp_path,
        "patient_id,read_id,arm",
        "p1,r1,control\np1,r2,control\np2,r3,control\n",
    )
    path = write_config({"data.units": _ARM_MEASURED_UNITS})
    assert "E-DATA-ASSIGN-VARIES" not in codes(path)


def test_validate_reports_rather_than_raising_on_a_varying_arm(write_config, tmp_path):
    """`validate` collects findings and never raises. The same `except
    ContractError` in `_check_units` that catches the cluster/weight raise
    catches this one too, and calling `validate_config` directly proves nothing
    escaped it."""
    _clustered_table(
        tmp_path,
        "patient_id,read_id,arm",
        "p1,r1,control\np1,r2,treatment\n",
    )
    path = write_config({"data.units": _ARM_MEASURED_UNITS})
    c = Collector()
    validate_config(path, c)
    assert any(f.code == "E-DATA-ASSIGN-VARIES" for f in c.findings)


# --- `k` and `k: all` are bounded by clusters -------------------------------
#
# `reference.md` § Validation, *Folds fit inside the clusters* and
# *Leave-one-out is affordable*. `E-DATA-CLUSTER-UNSUPPORTED` was live when these
# were written, so each asserted that refusal BESIDE the fold finding to prove the
# check was reached rather than shadowed. It is retired, so each now asserts the
# **exact** finding set instead — an empty one where the design is legal — which
# proves the same thing more strongly: a clustered config that validates clean is
# a clean config, not one whose findings were filtered.
#
# The roster is 7/3/3/1/1 over 15 units: 5 clusters, 15 units, two numbers that
# cannot be mistaken for each other. One unit per cluster would make the two
# equal and every assertion here vacuous.
_UNEVEN_SITES = "".join(f"p{i},{s}\n" for i, s in enumerate("aaaaaaabbbcccde"))

_CLUSTERED_UNITS = {
    "from": "index.csv",
    "key": "patient_id",
    "attributes": ["site"],
    "cluster_by": "site",
}
_UNCLUSTERED_UNITS = {"from": "index.csv", "key": "patient_id", "attributes": ["site"]}


def test_k_above_the_cluster_count_is_refused_through_validate(write_config, tmp_path):
    """§ Validation, *Folds fit inside the clusters*: `k: 10` over 5 clusters.

    The finding set is asserted exactly: `E-REPL-FOLD-K-TOO-LARGE` and nothing
    else, so a clustered declaration no longer drags a refusal along with it, and
    the sibling below is the control — the same roster and the same `k` with
    `cluster_by` gone reports nothing at all.
    """
    _clustered_table(tmp_path, "patient_id,site", _UNEVEN_SITES)
    found = codes(
        write_config(
            {
                "data.units": _CLUSTERED_UNITS,
                "replication": {"repeats": [{"kind": "fold", "k": 10}]},
            }
        )
    )
    assert found == {"E-REPL-FOLD-K-TOO-LARGE"}


def test_the_same_k_is_accepted_over_the_same_units_undeclared(write_config, tmp_path):
    """The control that must report. The roster is byte-identical and `k` is
    unchanged; only `cluster_by` is gone, and 10 folds over 15 independent units is
    a legal design. Without this, narrowing the basis to something wrong — or to a
    constant — would still pass the refusal above."""
    _clustered_table(tmp_path, "patient_id,site", _UNEVEN_SITES)
    found = codes(
        write_config(
            {
                "data.units": _UNCLUSTERED_UNITS,
                "replication": {"repeats": [{"kind": "fold", "k": 10}]},
            }
        )
    )
    # `site` undeclared over this roster is exactly what
    # `W-DATA-CLUSTER-UNDECLARED` looks for, and it is the whole finding set: the
    # fold check is silent, which is the point.
    assert found == {"W-DATA-CLUSTER-UNDECLARED"}


def test_leave_one_cluster_out_is_costed_in_clusters(write_config, tmp_path):
    """§ Validation, *Leave-one-out is affordable*: the budget is counted over the
    cluster count when `cluster_by` is declared. 1 condition × 5 clusters = 5
    executions against a budget of 8, so no warning — and the sibling below is the
    same config unclustered, where the same `k: all` is 15 and does warn."""
    _clustered_table(tmp_path, "patient_id,site", _UNEVEN_SITES)
    found = codes(
        write_config(
            {
                "data.units": _CLUSTERED_UNITS,
                "replication": {"repeats": [{"kind": "fold", "k": "all"}]},
                "limits": {"max_executions": 8},
            }
        )
    )
    assert found == set()


def test_leave_one_out_is_costed_in_units_when_nothing_is_clustered(
    write_config, tmp_path
):
    """The control that must report: the same roster and the same `k: all` with no
    `cluster_by` is 15 executions against the same budget of 8, and warns. The two
    together are what pin `k: all` to the cluster count rather than to the roster
    size — a budget that read the roster either way would fail this pair."""
    _clustered_table(tmp_path, "patient_id,site", _UNEVEN_SITES)
    found = messages_by_code(
        write_config(
            {
                "data.units": _UNCLUSTERED_UNITS,
                "replication": {"repeats": [{"kind": "fold", "k": "all"}]},
                "limits": {"max_executions": 8},
            }
        )
    )
    assert "W-EXEC-BUDGET" in found
    assert "15 executions exceeds 8" in found["W-EXEC-BUDGET"]


def test_the_cluster_bound_is_reported_by_a_direct_call_too(write_config, tmp_path):
    """Called directly, with no config file around it: the basis is the one number
    `validate_config` resolves through `units.fold_basis`, and the refusal names the
    clusters it counted rather than a unit count nobody supplied."""
    from publishable.templates.builtin.generic import GenericTemplate
    from publishable.validate import _check_replication

    doc = {
        "data": {"units": dict(_CLUSTERED_UNITS)},
        "replication": {"repeats": [{"kind": "fold", "k": 10}]},
    }
    c = Collector()
    _check_replication(doc, GenericTemplate(), c, fold_basis=5)
    reported = [f for f in c.findings if f.code == "E-REPL-FOLD-K-TOO-LARGE"]
    assert len(reported) == 1
    assert "5 clusters of `site`" in reported[0].message

    # ...and the same declaration over an unclustered basis of 15 is legal.
    control = Collector()
    _check_replication(
        {"replication": doc["replication"]}, GenericTemplate(), control, fold_basis=15
    )
    assert "E-REPL-FOLD-K-TOO-LARGE" not in {f.code for f in control.findings}


def test_the_repeat_floor_counts_a_clustered_k_all_in_clusters_too(write_config):
    """`_check_replication`'s *other* consumer of the basis. The refusal above goes
    through `resolve_repeats`; `W-REPL-FLOOR` goes through `_level_count`, and the
    two must read the same number or a design's repeat total means one thing to the
    floor and another to the fold it executes.

    `generic`'s `default_repeats` is 1, which no positive count can fall below, so
    this needs a template that sets a floor — the same `ThreeRepeats` construction
    the unclustered floor test uses.
    """
    from publishable.templates.builtin.generic import GenericTemplate
    from publishable.validate import _check_replication

    class ThreeRepeats(GenericTemplate):  # type: ignore[misc]
        default_repeats = 3

    doc = {
        "data": {"units": dict(_CLUSTERED_UNITS)},
        "replication": {"repeats": [{"kind": "fold", "k": "all"}]},
    }
    two_clusters = Collector()
    _check_replication(doc, ThreeRepeats(), two_clusters, fold_basis=2)
    assert "W-REPL-FLOOR" in {f.code for f in two_clusters.findings}

    # The control that must report: the same declaration over the 15-unit basis
    # those 2 clusters hold is 15 repeats, well above the floor. A floor reading
    # the roster where the fold reads the clusters would warn here too.
    fifteen_units = Collector()
    _check_replication(doc, ThreeRepeats(), fifteen_units, fold_basis=15)
    assert "W-REPL-FLOOR" not in {f.code for f in fifteen_units.findings}


def test_an_unreadable_cluster_leaves_k_all_unresolved_rather_than_raising(
    write_config, tmp_path
):
    """`cluster_by` names a column the roster carries but `attributes` never
    declared, so resolution never read it and `units.fold_basis` raises
    `E-DATA-CLUSTER-UNKNOWN`. `validate` collects and never raises: the basis is
    unresolved, `k: all` reports `E-REPL-FOLD-K` — honest, the fold count genuinely
    cannot be known — and the cluster finding beside it says why."""
    _clustered_table(tmp_path, "patient_id,site", _UNEVEN_SITES)
    c = Collector()
    validate_config(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id", "cluster_by": "site"},
                "replication": {"repeats": [{"kind": "fold", "k": "all"}]},
            }
        ),
        c,
    )
    found = {f.code for f in c.findings}
    assert "E-DATA-CLUSTER-UNKNOWN" in found
    assert "E-REPL-FOLD-K" in found


# --- a fold's `stratify_by` ---------------------------------------------------
#
# `E-REPL-FOLD-STRATIFY-UNSUPPORTED` was live when these were written —
# `resolve_repeats` refused any fold `stratify_by` before it read `k` at all — so
# every probe asserted the refusal appeared *with* the finding, as the proof the
# check was reached rather than shadowed. It is retired, so each probe asserts the
# **exact** finding set instead, which proves the same thing without leaning on a
# code that no longer exists. Each check is also exercised by a direct call.
#
# Only a `fold` level's `stratify_by` is checked here. § Validation's
# "Stratification attribute exists" row names no particular one, and its
# `data.units.assign.*.stratify_by` and `data.units.holdout.stratify_by` halves
# belong to the slices that build those blocks.

_ANIMAL_HEADER = "cell_id,animal_id,label"
_ANIMAL_SIZES = {"A1": 7, "A2": 3, "A3": 3, "A4": 1, "A5": 1}
_ANIMAL_LABELS = {"A1": "tumor", "A2": "normal", "A3": "tumor", "A4": "normal", "A5": "tumor"}


def _animal_body(varying: bool) -> str:
    """15 cells over 5 animals, sized 7/3/3/1/1, with `label` per animal.

    Neither coincidence that would make the clustering check unfireable holds:
    three of the animals hold several cells, so a stratum is not constant within a
    cluster merely for the cluster being a singleton, and `label` takes both values
    across the roster, so it is not constant globally either. `varying` flips one
    cell of the three-cell animal `A3` — one character between the probe and its
    control.
    """
    rows = []
    for animal, n in _ANIMAL_SIZES.items():
        for i in range(n):
            label = _ANIMAL_LABELS[animal]
            if varying and animal == "A3" and i == 0:
                label = "normal"
            rows.append(f"{animal}_{i},{animal},{label}")
    return "".join(f"{r}\n" for r in rows)


def _animal_config(write_config, tmp_path, *, varying: bool, attributes: list[str], **units):
    """The roster and the config together, so **one argument decides both**.

    `varying` writes the table as well as being the probe/control switch. Writing
    the table beside the config from each test would let a `varying=True` probe be
    paired with a `varying=False` roster — in a fixture whose whole discriminating
    power is one cell's label, that is a probe silently testing the control.
    """
    _clustered_table(tmp_path, _ANIMAL_HEADER, _animal_body(varying=varying))
    decl = {"from": "index.csv", "key": "cell_id", "attributes": attributes}
    decl.update(units)
    return write_config(
        {
            "data.units": decl,
            "replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "label"}]},
        }
    )


def test_a_fold_stratify_by_naming_no_attribute_is_reported(write_config, tmp_path):
    """§ Validation, "Stratification attribute exists", at a `fold` level:
    `stratify_by: label` is not in `data.units.attributes`, so the partitioner has
    nothing to balance the folds on."""
    found = codes(_animal_config(write_config, tmp_path, varying=False, attributes=["animal_id"]))
    # `W-DATA-CLUSTER-UNDECLARED` rides along: `animal_id` is a column of repeated
    # non-numeric labels and nothing declares it a cluster, which is exactly that
    # warning's trigger. Asserted as part of the exact set rather than filtered out.
    assert found == {"E-REPL-FOLD-STRATIFY-UNKNOWN", "W-DATA-CLUSTER-UNDECLARED"}


def test_a_declared_fold_stratum_is_not_reported_unknown(write_config, tmp_path):
    """The control that must report: the same roster and the same level, with
    `label` declared — the one difference the check is allowed to read."""
    found = codes(
        _animal_config(write_config, tmp_path, varying=False, attributes=["animal_id", "label"])
    )
    assert found == {"W-DATA-CLUSTER-UNDECLARED"}


def test_the_fold_stratum_name_check_reports_without_a_roster():
    """Direct, and with no roster at all:
    the name is read from the declaration, `_check_cluster_by`'s construction."""
    c = Collector()
    _check_fold_stratify_by(
        {"replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "label"}]}},
        {"attributes": ["age"]},
        None,
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-REPL-FOLD-STRATIFY-UNKNOWN"]
    clean = Collector()
    _check_fold_stratify_by(
        {"replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "label"}]}},
        {"attributes": ["label"]},
        None,
        None,
        clean,
    )
    assert not clean.findings


@pytest.mark.parametrize("declared", ["", [], ["label"], 3])
def test_a_fold_stratify_by_that_is_no_attribute_name_is_reported(declared):
    """Totality. `envelope.LEAF_TYPES` types `replication.repeats` a `list` and
    nothing inside a level, so unlike `data.units.cluster_by` there is no
    `E-CONFIG-TYPE` backstop for a non-string here: a fold stratifies on one
    attribute named as a string, and the list form the `holdout`, `assign` and
    `resample` blocks take is reported rather than silently accepted. An empty
    declaration names nothing and changes no behavior, the fault an empty
    `cluster_by` is reported for."""
    c = Collector()
    _check_fold_stratify_by(
        {"replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": declared}]}},
        {"attributes": ["label"]},
        None,
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-REPL-FOLD-STRATIFY-UNKNOWN"]


def test_a_level_with_no_stratify_by_is_not_reported():
    """The `None` control: `init` writes no `stratify_by`, and the worked example
    declares none, so an absent key must reach neither check."""
    c = Collector()
    _check_fold_stratify_by(
        {"replication": {"repeats": [{"kind": "fold", "k": 2}, {"kind": "seed", "n": 5}]}},
        {"attributes": ["label"]},
        None,
        None,
        c,
    )
    assert not c.findings


def test_a_fold_stratum_varying_within_a_cluster_is_reported(write_config, tmp_path):
    """§ Validation, "Fold strata survive clustering": `{kind: fold, stratify_by:
    label}` with `cluster_by: animal_id`, and `label` varies within animal `A3` — a
    stratum can't be balanced across a split that can't divide the cluster carrying
    both values."""
    found = codes(
        _animal_config(
            write_config,
            tmp_path,
            varying=True,
            attributes=["animal_id", "label"],
            cluster_by="animal_id",
        )
    )
    assert found == {"E-REPL-FOLD-STRATIFY-VARIES"}


def test_a_fold_stratum_constant_within_every_cluster_is_accepted(write_config, tmp_path):
    """The control that must report: the same design over the same animals with
    `label` constant within each — one cell's label apart from the probe. A stratum
    that agrees inside every indivisible cluster is exactly what a cluster-respecting
    stratified fold can satisfy, so it is not refused."""
    found = codes(
        _animal_config(
            write_config,
            tmp_path,
            varying=False,
            attributes=["animal_id", "label"],
            cluster_by="animal_id",
        )
    )
    assert found == set()


def test_the_fold_stratum_clustering_check_runs_on_a_direct_call():
    """Direct, over a hand-built roster: the same check without a config file, so
    a fixture that stopped resolving could not make this pass by silence."""
    doc = {"replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "label"}]}}
    decl = {"attributes": ["animal_id", "label"], "cluster_by": "animal_id"}
    varying = UnitList(
        [
            Unit(key="c0", paths=(), attributes={"animal_id": "A3", "label": "tumor"}),
            Unit(key="c1", paths=(), attributes={"animal_id": "A3", "label": "normal"}),
        ]
    )
    c = Collector()
    _check_fold_stratify_by(doc, decl, varying, "animal_id", c)
    assert [f.code for f in c.findings] == ["E-REPL-FOLD-STRATIFY-VARIES"]
    assert "A3" in c.findings[0].message
    constant = UnitList(
        [
            Unit(key="c0", paths=(), attributes={"animal_id": "A3", "label": "tumor"}),
            Unit(key="c1", paths=(), attributes={"animal_id": "A3", "label": "tumor"}),
        ]
    )
    clean = Collector()
    _check_fold_stratify_by(doc, decl, constant, "animal_id", clean)
    assert not clean.findings


def test_a_fold_stratum_naming_the_measurement_axis_is_reported(write_config, tmp_path):
    """The hole task 11 named in `cli` and called unreachable, which task 12's
    retirement of `E-REPL-FOLD-STRATIFY-UNSUPPORTED` made reachable.

    `collapse_measurements` consumes `data.units.measurements.by`, so `rep` is a
    declared attribute that no *resolved* unit carries — and `cli` rebuilds the
    strata from the collapsed roster, where the subscript reached a bare `KeyError`
    rather than a diagnostic. Reported under the name code because that is the fault
    it already describes: the reference set is `attributes` rather than the source's
    columns *because* a stratum has to survive resolution."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,rep,val\n" + "".join(f"u{i},r{j},{i}\n" for i in range(6) for j in range(2))
    )
    path = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["rep", "val"],
                "measurements": {"by": "rep", "collapse": "first"},
            },
            "replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "rep"}]},
        }
    )
    found = codes(path)
    assert "E-REPL-FOLD-STRATIFY-UNKNOWN" in found
    assert "measurements.by" in messages_by_code(path)["E-REPL-FOLD-STRATIFY-UNKNOWN"]
    # The control that must report clean: the identical config stratifying on the
    # other declared attribute, which does survive the collapse. Without it this
    # could not tell "the measurement axis is refused" from "any `stratify_by`
    # beside a `measurements` block is".
    clean = write_config(
        {
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["rep", "val"],
                "measurements": {"by": "rep", "collapse": "first"},
            },
            "replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "val"}]},
        }
    )
    assert "E-REPL-FOLD-STRATIFY-UNKNOWN" not in codes(clean)


def test_the_measurement_axis_stratum_check_runs_on_a_direct_call():
    """Direct, with no roster: both halves come from the declaration, which is why
    this is a `validate` check and not the run-time raise `E-DATA-CLUSTER-VARIES` is
    for the same declaration shape under `cluster_by` — that one needs the
    pre-collapse rows in hand to prove the disagreement, and this one needs
    nothing."""
    doc = {"replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "rep"}]}}
    decl = {"attributes": ["rep"], "measurements": {"by": "rep", "collapse": "first"}}
    c = Collector()
    _check_fold_stratify_by(doc, decl, None, None, c)
    assert [f.code for f in c.findings] == ["E-REPL-FOLD-STRATIFY-UNKNOWN"]
    # A `measurements` block of the wrong shape must not shadow this into a
    # traceback: `E-DATA-MEASUREMENTS-INVALID` owns that fault, and the axis is
    # simply unreadable here, so the stratum is left alone.
    loose = Collector()
    _check_fold_stratify_by(doc, {"attributes": ["rep"], "measurements": "rep"}, None, None, loose)
    assert not loose.findings


def test_a_varying_stratum_is_not_reported_without_a_cluster_by():
    """Nothing is indivisible without `cluster_by`, so the same varying `label` is
    a perfectly satisfiable stratification — the row is about the interaction, not
    about the attribute."""
    c = Collector()
    _check_fold_stratify_by(
        {"replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "label"}]}},
        {"attributes": ["animal_id", "label"]},
        UnitList(
            [
                Unit(key="c0", paths=(), attributes={"animal_id": "A3", "label": "tumor"}),
                Unit(key="c1", paths=(), attributes={"animal_id": "A3", "label": "normal"}),
            ]
        ),
        None,
        c,
    )
    assert not c.findings


def test_an_undeclared_fold_stratum_is_not_also_reported_as_varying():
    """One finding, not two: the reader has to declare the attribute either way, and
    a derived second fault on top of it is what `_check_cluster_by`'s own comment
    argues against."""
    c = Collector()
    _check_fold_stratify_by(
        {"replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "label"}]}},
        {"attributes": ["animal_id"], "cluster_by": "animal_id"},
        UnitList(
            [
                Unit(key="c0", paths=(), attributes={"animal_id": "A3", "label": "tumor"}),
                Unit(key="c1", paths=(), attributes={"animal_id": "A3", "label": "normal"}),
            ]
        ),
        "animal_id",
        c,
    )
    assert [f.code for f in c.findings] == ["E-REPL-FOLD-STRATIFY-UNKNOWN"]


def test_an_unreadable_cluster_leaves_the_stratum_check_silent_rather_than_raising():
    """`validate` collects and never raises. `clusters_of` raises
    `E-DATA-CLUSTER-UNKNOWN` for a unit carrying no cluster value, and that finding
    is already reported beside this check, so an unreadable grouping is silence here
    rather than a traceback."""
    c = Collector()
    _check_fold_stratify_by(
        {"replication": {"repeats": [{"kind": "fold", "k": 2, "stratify_by": "label"}]}},
        {"attributes": ["animal_id", "label"], "cluster_by": "animal_id"},
        UnitList(
            [
                Unit(key="c0", paths=(), attributes={"animal_id": "A3", "label": "tumor"}),
                Unit(key="c1", paths=(), attributes={"label": "normal"}),
            ]
        ),
        "animal_id",
        c,
    )
    assert not c.findings


# --- what `_fold_k` reports now that its stratify refusal is gone --------------
#
# Task 6 pinned these two as the *pre*-flip expectations, asserting the flip code
# was ABSENT, precisely so that retiring `E-REPL-FOLD-STRATIFY-UNSUPPORTED` — a
# raise that sat ahead of every read of `k` — turned them over visibly in the diff
# rather than being discovered afterwards. H3b task 12 retired it, and these are
# the post-flip expectations. **Kept as pins rather than deleted**: what they
# record is that this reordering happened, and that each config's surviving fault
# is the one that was always there behind the refusal.
#
# `W-DATA-CLUSTER-UNDECLARED` rides along in both: `animal_id` is a column of
# repeated non-numeric labels that nothing declares a cluster. Asserted as part of
# the exact set rather than filtered out, so the flip is pinned against the whole
# finding set and not against one member of it.


def test_a_fold_stratify_by_reports_before_an_illegal_k(write_config, tmp_path):
    """`{k: 1, stratify_by: label}` reported the stratify refusal and *not*
    `E-REPL-FOLD-K` until task 12 retired that refusal. It now reports
    `E-REPL-FOLD-K`: `k: 1` is not a partition into folds, and that was true all
    along behind a refusal that returned before `k` was read."""
    _clustered_table(tmp_path, _ANIMAL_HEADER, _animal_body(varying=False))
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "cell_id",
                    "attributes": ["animal_id", "label"],
                },
                "replication": {"repeats": [{"kind": "fold", "k": 1, "stratify_by": "label"}]},
            }
        )
    )
    assert found == {"E-REPL-FOLD-K", "W-DATA-CLUSTER-UNDECLARED"}


def test_a_fold_stratify_by_reports_before_an_oversized_k(write_config, tmp_path):
    """`{k: 99, stratify_by: label}` over a 15-unit roster reported the stratify
    refusal and *not* `E-REPL-FOLD-K-TOO-LARGE` until task 12 retired that refusal.
    It now reports `E-REPL-FOLD-K-TOO-LARGE`. The roster is well under 99, so the
    flip this pinned was genuinely reachable rather than a hypothetical."""
    _clustered_table(tmp_path, _ANIMAL_HEADER, _animal_body(varying=False))
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "cell_id",
                    "attributes": ["animal_id", "label"],
                },
                "replication": {"repeats": [{"kind": "fold", "k": 99, "stratify_by": "label"}]},
            }
        )
    )
    assert found == {"E-REPL-FOLD-K-TOO-LARGE", "W-DATA-CLUSTER-UNDECLARED"}


def test_the_one_level_control_arm_baseline_reports_where_it_once_validated_clean(
    write_config, tmp_path
):
    """The defect end to end, on the config that carried it: a well-formed
    `between` + `by_attribute` design over one `control` level, whose baseline
    designates that arm the way § Group axes used to tell a reader to.

    Driven before this refusal existed, `validate` reported **zero findings** and
    `run` exited 0 while `conditions/00_baseline` and `conditions/01_arm=control`
    came out byte-identical at every file — the same 8 units handed to both, on
    all five seed repeats. Nothing else in the suite reaches that config: at two
    levels `E-DATA-ALLOCATION-CONTRAST` masks it, and at one level there is no
    cross-arm comparison for that code to read.

    `test_by_attribute_assignment_is_accepted` is the control that must stay
    silent — the same fixture without the baseline, whose finding set is empty —
    so an exact set of exactly one code here separates "the refusal fired" from
    "this config was never clean anyway"."""
    rows = "".join(f"p{i},control\n" for i in range(8))
    (tmp_path / "input" / "index.csv").write_text(f"patient_id,arm\n{rows}")
    design = _between({"arm": {"method": "by_attribute"}}, attributes=["arm"])
    design["sweep"] = {
        "groups": [{"by": "arm", "levels": ["control"]}],
        "baseline": {"arm": "control"},
    }
    assert _error_codes(write_config(design)) == {"E-SWEEP-BASELINE-GROUP"}


def test_a_baseline_may_not_fix_a_group_level(write_config):
    """`E-SWEEP-BASELINE-GROUP` — § Expansion modes: "the arms of a group axis
    are peers, and `sweep.baseline` may not fix one of them".

    Unrefused, `_baseline_cells` reads the fixed axis as fixed and expands over
    nothing while `_axes` still emits that level as a product row, so the level
    is rendered **twice**. Driven end to end over a roster of 8 `control` units,
    `conditions/00_baseline` and `conditions/01_arm=control` came out
    byte-identical at every file, across all five seed repeats, with `validate`
    reporting zero findings and `run` exiting 0 — `experimental-designs.md`
    § Mistakes core prevents' *two identical measurements reported as two arms*,
    verbatim. At two or more levels `E-DATA-ALLOCATION-CONTRAST` fires beside
    it, which is why the one-level shape below is asserted as its own exact set:
    that refusal is temporary (it lifts with the unpaired estimator family) and
    at one level it reaches nothing.

    A group level is still not a parameter path, so `_path_resolves` must not
    ask `parameter_spec` about it — this reports the level, never
    `E-SWEEP-PATH-UNKNOWN`, and `_value_checks` is never handed a path
    `spec[path]` would `KeyError` on.

    Four controls, each of which must report something different:

    * a baseline fixing only a *parameter* path beside a group axis is the legal
      shape § Expansion modes tells a reader to write, and stays legal — it
      expands over the axis, one reference per arm;
    * with no `groups` axis declaring `arm`, the same baseline key *is* an
      unknown parameter path and stays `E-SWEEP-PATH-UNKNOWN`, so the gate is
      the declared axis name rather than the `groups` block's presence;
    * a misspelled parameter path beside a real group axis is still reported;
    * and `ablate` takes the sibling code instead, never both, since what goes
      wrong there is that the other levels execute nowhere rather than that this
      one executes twice (`expand`'s `crossed` branch emits no product rows).
      Crossed with a *parameter* axis, `crossed` is False and the level is
      duplicated after all — that shape carries `E-SWEEP-ABLATE-CROSSED` for its
      own reason, and its three-code set is pinned here so the co-report is not
      something a later reader has to re-derive.

    `E-DATA-ALLOCATION-WITHIN-ARMS` is expected beside the codes under test
    rather than filtered away: `validate` collects rather than stops, and none
    of these configs declares `allocation`, which defaults to `within`, beside a
    declared group axis."""
    axis = [{"by": "arm", "levels": ["control", "treatment"]}]
    one_level = [{"by": "arm", "levels": ["control"]}]

    # The defect itself, at the one-level shape nothing else touches.
    assert _error_codes(
        write_config({"sweep": {"groups": one_level, "baseline": {"arm": "control"}}})
    ) == {
        "E-SWEEP-BASELINE-GROUP",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }
    message = messages_by_code(
        write_config({"sweep": {"groups": one_level, "baseline": {"arm": "control"}}})
    )["E-SWEEP-BASELINE-GROUP"]
    assert "arm" in message
    assert "twice" in message

    # And at two levels, where the temporary cross-arm refusal fires beside it.
    assert _error_codes(
        write_config({"sweep": {"groups": axis, "baseline": {"arm": "control"}}})
    ) == {
        "E-SWEEP-BASELINE-GROUP",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
        "E-DATA-ALLOCATION-CONTRAST",
    }

    # Control 1: a parameter-path baseline beside the same axis is legal.
    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": axis,
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                    "baseline": {"analysis.method": "pearson"},
                }
            }
        )
    ) == {"E-DATA-ALLOCATION-WITHIN-ARMS"}

    # Control 2: no axis declares `arm`, so the key is an unknown parameter path.
    assert _error_codes(write_config({"sweep": {"baseline": {"arm": "control"}}})) == {
        "E-SWEEP-PATH-UNKNOWN"
    }

    # Control 3: a misspelled parameter path beside a real axis is still checked.
    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": axis,
                    "baseline": {"arm": "control", "analysis.methdo": "pearson"},
                }
            }
        )
    ) == {
        "E-SWEEP-BASELINE-GROUP",
        "E-SWEEP-PATH-UNKNOWN",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
        "E-DATA-ALLOCATION-CONTRAST",
    }

    # Control 4: `ablate` takes the sibling code alone, and the parameter-axis
    # cross takes it beside `E-SWEEP-ABLATE-CROSSED`.
    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": axis,
                    "baseline": {"arm": "control", "analysis.drop_missing": True},
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        )
    ) == {
        "E-SWEEP-ABLATE-BASELINE-GROUP",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }

    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": axis,
                    "grid": {"analysis.method": ["spearman", "kendall"]},
                    "baseline": {"arm": "control", "analysis.drop_missing": True},
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        )
    ) == {
        "E-SWEEP-ABLATE-BASELINE-GROUP",
        "E-SWEEP-ABLATE-CROSSED",
        "E-DATA-ALLOCATION-CONTRAST",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }


def test_two_group_axes_may_not_share_a_name(write_config):
    """§ Validation's *Axis names are distinct* — a shape `selector_paths`'
    dedup hides from the group-vs-parameter check above, since that check reads
    `selector_paths(sweep)`, which is total over a malformed block and dedupes
    two same-named entries into one axis name. Left unchecked, `sweep._axes`
    still builds one axis per *entry* regardless — verified directly against
    `sweep.expand`, not assumed: two `arm` entries with disjoint levels
    (`[a, b]` and `[c, d]`) cross into four conditions whose labels collapse to
    two (`arm=a`/`arm=b` from the first axis' cells, overwritten by
    `arm=c`/`arm=d` from the second's, both pairs rendering as just `arm=c` and
    `arm=d`), not the four distinct cells the declaration names.

    The control must report only *Arms need allocation* (no `allocation`
    declared): two *distinct* group axes is the ordinary composed design this
    check must not also flag."""
    from publishable.sweep import expand

    doc = {
        "sweep": {
            "groups": [
                {"by": "arm", "levels": ["a", "b"]},
                {"by": "arm", "levels": ["c", "d"]},
            ]
        }
    }
    labels = [c.label for c in expand(doc)]
    assert len(labels) == 4
    assert len(set(labels)) == 2  # the defect: four cells, two labels

    assert _error_codes(write_config(doc)) == {
        "E-SWEEP-PATH-DUPLICATE",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }

    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": [
                        {"by": "arm", "levels": ["a", "b"]},
                        {"by": "cohort", "levels": ["c", "d"]},
                    ]
                }
            }
        )
    ) == {"E-DATA-ALLOCATION-WITHIN-ARMS"}


def test_a_group_axis_may_not_name_a_path_a_parameter_axis_writes(write_config):
    """`groups: [{by: arm}]` beside `grid: {arm: [...]}` is worse than the
    overwrite `E-SWEEP-PATH-DUPLICATE` already refuses between two parameter
    axes: `expand` marks the path a *selector* on every row, so
    `resolve_condition_cfg` plants nothing and `cli`'s wide config subtracts it —
    the grid axis claims to sweep `parameters.arm` while every condition runs the
    base value at every scope. That is § Mistakes core prevents' "a typo'd
    parameter silently using a default", reached by a route no other check
    covers: the duplicate check reads `grid`/`paired`/`sample` only.

    The control must report: a group axis whose name no parameter axis writes is
    the ordinary composed design, and carries *Arms need allocation* alone —
    neither config below declares `allocation`, which defaults to `within`,
    beside the declared `arm` axis."""
    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": [{"by": "arm", "levels": ["control", "treatment"]}],
                    "grid": {"arm": ["control", "treatment"]},
                }
            }
        )
    ) == {
        "E-SWEEP-PATH-DUPLICATE",
        "E-SWEEP-PATH-UNKNOWN",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }

    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": [{"by": "arm", "levels": ["control", "treatment"]}],
                    "grid": {"analysis.method": ["pearson", "spearman"]},
                }
            }
        )
    ) == {"E-DATA-ALLOCATION-WITHIN-ARMS"}


def test_a_group_axis_may_not_name_a_declared_parameter_even_if_unswept(write_config):
    """The addendum's correction to this task's own brief: the swept-collision
    test above only reaches `path in named_by`, built from `grid`/`paired`/`sample`
    entries alone — so a `by` naming a path this template declares as a *parameter*
    but which no OTHER axis-shaped mode sweeps slipped past every check, and
    probing it directly before this fix landed drew only
    `E-DATA-ALLOCATION-WITHIN-ARMS`, none of the `sweep.groups` § Validation rows.
    Task 5's ruling — the one the addendum's Step 2 originally proposed minting a
    second code for — turned out already correct in substance, just narrower than
    it needed to be: extending the existing `E-SWEEP-PATH-DUPLICATE` check to read
    `spec` (`template.parameter_spec`, the same reference `_path_resolves` checks
    a `grid`/`baseline` path against) rather than only `named_by` is the fix.

    The harm survives unswept, which is why this is a real gap and not a
    stylistic one: `expand` still marks `analysis.method` a selector on this row
    (asserted directly, not inferred from the refusal alone), so
    `resolve_condition_cfg` still skips planting it — condition
    `method=spearman`'s own resolved config keeps `analysis.method: "pearson"`,
    the base value, while its label and directory claim `spearman`. That is
    indistinguishable from a real swept parameter to a reader who has not opened
    `sweep.yaml`'s `values`, and is the argument for refusing it even though no
    *other* axis loses a value the way the already-built swept case does.

    The control: `by: cohort` names no parameter this template declares (only
    the four `analysis.*` paths are), so the ordinary composed groups design —
    no `allocation` declared beside it — reports *Arms need allocation* alone,
    proving the new check does not fire on every group axis."""
    from publishable.runner import resolve_condition_cfg

    doc = {"sweep": {"groups": [{"by": "analysis.method", "levels": ["pearson", "spearman"]}]}}
    conditions = expand(doc)
    spearman = next(c for c in conditions if c.label == "method=spearman")
    assert spearman.selectors == {"analysis.method"}
    resolved = resolve_condition_cfg(
        {"parameters": {"analysis": {"method": "pearson"}}}, spearman
    )
    assert resolved.parameters.analysis.method == "pearson"  # not "spearman"

    assert _error_codes(write_config(doc)) == {
        "E-SWEEP-PATH-DUPLICATE",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }

    assert _error_codes(
        write_config({"sweep": {"groups": [{"by": "cohort", "levels": ["a", "b"]}]}})
    ) == {"E-DATA-ALLOCATION-WITHIN-ARMS"}


def test_a_group_level_must_render_into_a_condition_label(write_config):
    """A group cell renders into a label now that the axis expands
    (`00_arm=control`), and a label is also a directory segment and a selector.
    `control__b` passes `SWEEP_VALUE_PATTERN` and destroys the axis separator, so
    it is refused exactly as a `grid` value is — the exemption `sweep.baseline`
    values get never applied to a value `label_for` renders.

    The control must report: well-formed levels carry *Arms need allocation*
    alone — none of these three configs declares `allocation`, which defaults
    to `within`, beside the declared `arm` axis."""
    assert _error_codes(
        write_config(
            {"sweep": {"groups": [{"by": "arm", "levels": ["control", "treat__ment"]}]}}
        )
    ) == {
        "E-SWEEP-VALUE-UNNAMEABLE",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }

    assert _error_codes(
        write_config({"sweep": {"groups": [{"by": "arm", "levels": ["control", "a/b"]}]}})
    ) == {
        "E-SWEEP-VALUE-UNNAMEABLE",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }

    assert _error_codes(
        write_config(
            {"sweep": {"groups": [{"by": "arm", "levels": ["control", "treatment"]}]}}
        )
    ) == {"E-DATA-ALLOCATION-WITHIN-ARMS"}


def test_a_baseline_may_not_fix_a_group_level_while_ablate_is_declared(write_config):
    """§ Expansion modes states this twice: "`sweep.baseline` may not fix a level
    of the group axis, here or anywhere else — the arms are peers — and this
    composition is the shape where the refusal bites hardest", and "`ablate ×
    groups` always lands in the second row, since `validate` rejects a baseline
    that fixes a group level: an ablation is one change from *its own cell's*
    full model, and there is no single reference condition when the reference
    cohort differs".

    The sibling code `E-SWEEP-BASELINE-GROUP` refuses the same declaration
    without `ablate`, and the two guards are mutually exclusive — every config
    here carries exactly one of them, which is what the exact sets pin.

    Unrefused, the declaration does not merely mis-number — **a declared level
    disappears from the run**. The baseline fixes the group axis, so it expands
    over nothing, the crossed ablation has one empty cell to repeat over, and
    `expand` returns `00_baseline` and `01_labs=false` on the derivation cohort
    alone: `validation` is executed nowhere while the run reports success.

    Two controls, both of which must report: an ablation whose baseline fixes a
    *parameter* beside the same group axis is the legal composition and carries
    *Arms need allocation* alone (it is also
    `test_ablate_composes_with_a_group_axis`, untouched), and the same fixed
    level *without* `ablate` takes `E-SWEEP-BASELINE-GROUP` rather than this
    code. None of the three declares `allocation`, which defaults to `within`,
    beside the declared `cohort` axis, so `E-DATA-ALLOCATION-WITHIN-ARMS` fires
    alongside every one of them.

    The second control also carries `E-DATA-ALLOCATION-CONTRAST`: its baseline
    fixes `cohort` to `derivation` and leaves `analysis.method` free, so
    `sweep.expand` renders one per-cell baseline per method value **within
    `derivation` alone** — `validation`'s two conditions have no baseline of
    their own and are compared against `derivation`'s, a cross-cohort,
    disjoint-units comparison for each. That is the generated route to that
    code, and it is reachable only from a baseline fixing a group level, which
    is exactly why it is co-reported with the sibling refusal here rather than
    standing alone."""
    axis = [{"by": "cohort", "levels": ["derivation", "validation"]}]
    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": axis,
                    "baseline": {"cohort": "derivation", "analysis.drop_missing": True},
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        )
    ) == {
        "E-SWEEP-ABLATE-BASELINE-GROUP",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
    }

    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": axis,
                    "baseline": {"analysis.drop_missing": True},
                    "ablate": {"remove": ["analysis.drop_missing"]},
                }
            }
        )
    ) == {"E-DATA-ALLOCATION-WITHIN-ARMS"}

    assert _error_codes(
        write_config(
            {
                "sweep": {
                    "groups": axis,
                    "grid": {"analysis.method": ["pearson", "spearman"]},
                    "baseline": {"cohort": "derivation"},
                }
            }
        )
    ) == {
        "E-SWEEP-BASELINE-GROUP",
        "E-DATA-ALLOCATION-WITHIN-ARMS",
        "E-DATA-ALLOCATION-CONTRAST",
    }


# `data.units.allocation`, `data.units.assign`, and `sweep.groups` against each
# other — § Validation's *Allocation needs arms*, *Every axis is assigned*, and
# *Assignment names a method*.
#
# Each assertion below is an exact set rather than a membership test, so a
# test asserting only that *some* error fired would not pass with the checks
# under test deleted. The direct-`_check_assign` tests below are the second
# half of the same discipline: they reach each check with nothing else
# running at all.

_ARM_AXIS = [{"by": "arm", "levels": ["control", "treatment"]}]


def _between(assign, axes=None, **extra) -> dict:
    """A `between` design with a group axis, for `write_config`'s dotted overrides."""
    units = {"from": "index.csv", "key": "patient_id", "allocation": "between", **extra}
    if assign is not None:
        units["assign"] = assign
    return {"data.units": units, "sweep": {"groups": _ARM_AXIS if axes is None else axes}}


def test_between_allocation_with_no_group_axis_has_no_arms(write_config):
    """§ Allocation: `between` "answers *how units reach an arm*, not *what the
    arms are*", so the declaration alone divides nothing.

    The control must report — it carries the one live refusal — so an exact-set
    assertion tells "the arms are declared" from "the check is dead"."""
    assert _error_codes(
        write_config({"data.units": {"from": "index.csv", "key": "patient_id",
                                     "allocation": "between"}})
    ) == {"E-DATA-ALLOCATION-NO-ARMS"}

    # `_between` declares no `data.units.attributes` at all, so `arm` — defaulted
    # from the axis name — resolves to no unit attribute either: a live code,
    # `E-DATA-ASSIGN-UNKNOWN`.
    assert _error_codes(
        write_config(_between({"arm": {"method": "by_attribute"}}))
    ) == {
        "E-DATA-ASSIGN-UNKNOWN",
    }


@pytest.mark.parametrize("assign", [None, {}, {"arm": None}])
def test_a_group_axis_with_no_assign_block_is_refused(write_config, assign):
    """The three shapes § The one config file's "REQUIRED when allocation is
    `between`" covers on this side: no `assign` key at all, an empty `assign: {}`
    — which is what `init` writes — and an axis key left null. All three leave
    `arm` unassigned, so all three report the same set — the same code that
    used to distinguish `{arm: None}` from the other two, `E-DATA-ASSIGN-UNSUPPORTED`
    (fired on a *truthy* `assign`, and `{arm: null}` was truthy while `{}` was
    not), retired with task 17."""
    assert _error_codes(write_config(_between(assign))) == {
        "E-DATA-ASSIGN-MISSING",
    }


def test_each_unassigned_axis_is_reported_on_its_own():
    """One finding per axis, in declaration order — a code set cannot tell one
    finding from two, and the remedy is one block per axis.

    Reached directly, with no refusal running beside it: `sex` is assigned and
    `arm` is not, so a check that reported per-*config* rather than per-axis
    would give one finding here and a check that ignored the assigned axis would
    give two."""
    c = Collector()
    _check_assign(
        {"sweep": {"groups": [{"by": "sex", "levels": ["f", "m"]},
                              {"by": "arm", "levels": ["control", "treatment"]}]}},
        {"allocation": "between", "assign": {"sex": {"method": "by_attribute"}}},
        None,
        c,
    )
    missing = [f for f in c.findings if f.code == "E-DATA-ASSIGN-MISSING"]
    assert len(missing) == 1
    assert "`arm`" in missing[0].message and "`sex`" not in missing[0].message


def test_within_allocation_with_a_group_axis_is_arms_need_allocation():
    """The mirror of `test_between_allocation_with_no_group_axis_has_no_arms`
    below: a group axis under the default `within` is *Arms need allocation*,
    `E-DATA-ALLOCATION-WITHIN-ARMS` — reporting a missing `assign` here instead
    would name the wrong fault, since `assign` means nothing under `within` at
    all. Read from the declarations alone, so it reports with no roster."""
    c = Collector()
    _check_assign({"sweep": {"groups": _ARM_AXIS}}, {"from": "index.csv"}, None, c)
    assert [f.code for f in c.findings] == ["E-DATA-ALLOCATION-WITHIN-ARMS"]

    # An explicit `allocation: within` is the same fault as the absent key that
    # defaults to it — the row is stated in terms of the *value*, not the key's
    # presence.
    c = Collector()
    _check_assign(
        {"sweep": {"groups": _ARM_AXIS}},
        {"from": "index.csv", "allocation": "within"},
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ALLOCATION-WITHIN-ARMS"]


def test_between_allocation_with_a_group_axis_draws_neither_arms_row(write_config, tmp_path):
    """The control the pair demands: `allocation: between` beside a well-formed
    group axis is the legal composition, so it must draw NEITHER
    `E-DATA-ALLOCATION-NO-ARMS` nor its mirror `E-DATA-ALLOCATION-WITHIN-ARMS`.

    Both halves assert the EXACT set, per this block's own stated convention
    three tests above ("Every config below still carries a live refusal, and
    that is why each assertion is an exact set rather than a membership test")
    — a membership-only assertion cannot tell "correctly silent" from "nothing
    ran": inserting a `return` at the top of `_check_assign` still passes one.
    `attributes: ["arm"]` (and, for `write_config`, an `arm` column in
    `index.csv`) is declared in both halves so the config is genuinely
    well-formed and carries no *other* live code either (`E-DATA-ASSIGN-UNKNOWN`
    would fire on an undeclared `arm` attribute regardless of roster,
    `_check_assign`'s own "read from the declaration" row)."""
    c = Collector()
    _check_assign(
        {"sweep": {"groups": _ARM_AXIS}},
        {
            "from": "index.csv",
            "allocation": "between",
            "attributes": ["arm"],
            "assign": {"arm": {"method": "by_attribute"}},
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == []
    # The positive sibling probe: the same declaration pair, under `within`
    # instead, must still report — proving the assertion above is not merely
    # "nothing ran" for this fixture shape.
    c = Collector()
    _check_assign(
        {"sweep": {"groups": _ARM_AXIS}},
        {"from": "index.csv", "attributes": ["arm"], "assign": {"arm": {"method": "by_attribute"}}},
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ALLOCATION-WITHIN-ARMS"]

    (tmp_path / "input" / "index.csv").write_text("patient_id,arm\np1,control\np2,treatment\n")
    found = _error_codes(
        write_config(_between({"arm": {"method": "by_attribute"}}, attributes=["arm"]))
    )
    assert found == set()


def test_by_attribute_assignment_is_accepted(write_config, tmp_path):
    """`by_attribute` is the one method that executes in this build, so it earns
    neither `E-DATA-ASSIGN-METHOD` (absent or out-of-enum) nor
    `E-DATA-ASSIGN-DRAWN` (in-enum but drawn) — the control for both. A
    well-formed `groups` + `allocation: between` + `assign` config now
    validates fully clean — task 17 retired the three `-UNSUPPORTED` refusals
    that used to be the only findings a config this well-formed carried, and
    `test_assign_levels_is_reported_through_a_real_validate_config` below is
    this test's can-fail control: the same fixture with one arm's row missing
    reports `E-DATA-ASSIGN-LEVELS`, so an empty set here is not "nothing ran".

    This is also the accept path for `from`/`levels`: `write_config`'s
    `index.csv` carries only `patient_id`, so an `arm` column is written here —
    one row per declared level, covering both — to exercise `E-DATA-ASSIGN-UNKNOWN`
    and `E-DATA-ASSIGN-LEVELS` resolving clean rather than merely being unreached."""
    (tmp_path / "input" / "index.csv").write_text("patient_id,arm\np1,control\np2,treatment\n")
    found = _error_codes(
        write_config(_between({"arm": {"method": "by_attribute"}}, attributes=["arm"]))
    )
    assert found == set()
    assert "E-DATA-ASSIGN-DRAWN" not in found
    assert "E-DATA-ASSIGN-METHOD" not in found
    assert "E-DATA-ASSIGN-UNKNOWN" not in found
    assert "E-DATA-ASSIGN-LEVELS" not in found


def test_assign_levels_is_reported_through_a_real_validate_config(write_config, tmp_path):
    """The direct `_check_assign` tests below all hand-build the `doc`/roster — this
    is the one end-to-end path, through `validate_config` and a resolved roster from
    a real `input_dir` CSV, so the wiring from `sweep.groups`' declared levels through
    a resolved column to `units.arms_of` is live rather than merely unreached by the
    control above. `treatment` is declared but no row names it — the can-fail control
    for `test_by_attribute_assignment_is_accepted`'s empty set."""
    (tmp_path / "input" / "index.csv").write_text("patient_id,arm\np1,control\np2,control\n")
    found = _error_codes(
        write_config(_between({"arm": {"method": "by_attribute"}}, attributes=["arm"]))
    )
    assert found == {"E-DATA-ASSIGN-LEVELS"}


def test_assign_from_defaults_to_the_axis_name():
    """§ The one config file: `from` is `by_attribute` only, and **defaults to
    the axis name**. No `from` key at all, axis named `arm`, attribute `arm`
    declared — the default is what makes this resolve, and reached directly
    (no `allocation`, no `sweep`) so nothing else in `_check_assign` can speak
    for it. Roster-free, `_check_weight_by`'s own construction: the name half
    runs from the declaration alone."""
    c = Collector()
    _check_assign(
        {},
        {"attributes": ["arm"], "assign": {"arm": {"method": "by_attribute"}}},
        None,
        c,
    )
    assert [f.code for f in c.findings] == []


def test_assign_from_default_is_reported_when_it_misses():
    """Paired with the test above — same config, but `data.units.attributes`
    does not list `arm`, so the very name the default produced is the one that
    fails to resolve. Discriminates the default from a check that never ran:
    a config omitting `from` passes the first test either way if the default
    is dead code, but only the real default produces a finding naming `arm`
    here. The message names the resolved value and says it was defaulted,
    since that string is the only observable evidence of which name the
    default produced."""
    c = Collector()
    _check_assign(
        {},
        {"attributes": ["site"], "assign": {"arm": {"method": "by_attribute"}}},
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-UNKNOWN"]
    assert c.findings[0].path == "data.units.assign.arm.from"
    assert "'arm'" in c.findings[0].message
    assert "defaulted from the axis name" in c.findings[0].message


def test_assign_from_declared_overrides_the_default_and_reports_its_own_name():
    """A declared `from` is read over the axis name, and the unknown message
    names the *declared* value rather than the axis — `'cohort_label'`, not
    `'arm'` — and does not claim a default that did not happen."""
    c = Collector()
    _check_assign(
        {},
        {
            "attributes": ["site"],
            "assign": {"arm": {"method": "by_attribute", "from": "cohort_label"}},
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-UNKNOWN"]
    assert "'cohort_label'" in c.findings[0].message
    assert "'arm'" not in c.findings[0].message
    assert "defaulted from the axis name" not in c.findings[0].message


def test_assign_from_a_non_string_is_reported_rather_than_skipped():
    """`assign.<axis>.from` is a dynamic key `envelope.py`'s `LEAF_TYPES` cannot
    type (unlike `weight_by`/`cluster_by`), so there is no `E-CONFIG-TYPE`
    backstop for a non-`str` value to defer to — a config shape `validate` would
    otherwise be silent about. Folded into `E-DATA-ASSIGN-UNKNOWN` rather than
    skipped, naming the value's type rather than a resolved attribute name."""
    c = Collector()
    _check_assign(
        {},
        {"attributes": ["arm"], "assign": {"arm": {"method": "by_attribute", "from": 3}}},
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-UNKNOWN"]
    assert c.findings[0].path == "data.units.assign.arm.from"
    assert "int" in c.findings[0].message
    assert "3" in c.findings[0].message


def test_assign_from_an_empty_string_matches_weight_bys_own_wording():
    """Present, not absent, so the axis-name default does not apply — the same
    shape `_check_weight_by` gives its own dedicated wording rather than the
    generic "resolves to ''" a name-lookup miss would otherwise produce."""
    c = Collector()
    _check_assign(
        {},
        {"attributes": ["arm"], "assign": {"arm": {"method": "by_attribute", "from": ""}}},
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-UNKNOWN"]
    assert "is empty" in c.findings[0].message
    assert "changes no behavior" in c.findings[0].message


def _arm_roster(values: list[str | None]) -> UnitList:
    """A roster of units keyed `u0`, `u1`, ... holding `arm` at the given value —
    `None` meaning the unit carries no value for it at all, `clusters_of`'s own
    missing-attribute case."""
    return UnitList(
        [
            Unit(key=f"u{i}", paths=(), attributes={"arm": v} if v is not None else {})
            for i, v in enumerate(values)
        ]
    )


def test_assign_levels_resolve_when_every_unit_names_a_declared_level():
    """The accept path for `E-DATA-ASSIGN-LEVELS`: three units, one level
    repeated. Deliberately not two units, one per level — that partition would
    coincide with a two-cluster fixture, and an arm-aware reader (grouping
    `control` twice) would be indistinguishable from a cluster-aware one, which
    has no notion of `levels` at all and would not even run this check."""
    c = Collector()
    _check_assign(
        {"sweep": {"groups": [{"by": "arm", "levels": ["control", "treatment"]}]}},
        {
            "attributes": ["arm"],
            "allocation": "between",
            "assign": {"arm": {"method": "by_attribute"}},
        },
        _arm_roster(["control", "control", "treatment"]),
        c,
    )
    assert [f.code for f in c.findings] == []


def test_assign_levels_refused_when_a_value_names_no_declared_level():
    """§ Allocation, twice: `from` "a unit attribute whose values are exactly
    the declared levels", and `between` opens "each unit belongs to exactly
    one arm". A unit holding `unknown_arm` — not `control` or `treatment` —
    would belong to no arm, and there is no fourth part of `n` for it."""
    c = Collector()
    _check_assign(
        {"sweep": {"groups": [{"by": "arm", "levels": ["control", "treatment"]}]}},
        {
            "attributes": ["arm"],
            "allocation": "between",
            "assign": {"arm": {"method": "by_attribute"}},
        },
        _arm_roster(["control", "treatment", "unknown_arm"]),
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-LEVELS"]
    assert "unknown_arm" in c.findings[0].message


def test_assign_levels_refused_when_a_unit_carries_no_value_at_all():
    """The other route to the same violation `clusters_of` recognizes for
    `cluster_by`: a unit with no value for the attribute at all belongs to no
    arm exactly as one holding an unrecognized value does, so it is folded into
    the same code and message rather than a distinct one."""
    c = Collector()
    _check_assign(
        {"sweep": {"groups": [{"by": "arm", "levels": ["control", "treatment"]}]}},
        {
            "attributes": ["arm"],
            "allocation": "between",
            "assign": {"arm": {"method": "by_attribute"}},
        },
        _arm_roster(["control", "treatment", None]),
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-LEVELS"]
    assert "carries no value" in c.findings[0].message


def test_assign_levels_refused_when_a_declared_level_holds_no_unit():
    """The other direction of set equality: every unit resolves to a declared
    level, but one declared level — `treatment` — holds none of them, so that
    arm's condition would resolve zero units."""
    c = Collector()
    _check_assign(
        {"sweep": {"groups": [{"by": "arm", "levels": ["control", "treatment"]}]}},
        {
            "attributes": ["arm"],
            "allocation": "between",
            "assign": {"arm": {"method": "by_attribute"}},
        },
        _arm_roster(["control", "control", "control"]),
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-LEVELS"]
    assert "treatment" in c.findings[0].message


@pytest.mark.parametrize("method", ["random", "blocked"])
def test_a_drawn_assignment_method_is_refused(write_config, method):
    """`random` and `blocked` are both in `ASSIGN_METHODS`, so neither earns
    `E-DATA-ASSIGN-METHOD`; both draw an arm rather than reading one already
    assigned, which is what `E-DATA-ASSIGN-DRAWN` refuses. Parametrized rather
    than one test for both values, per the mutation requirement: narrowing the
    refused set to just one of them must fail exactly one of these two runs."""
    found = _error_codes(write_config(_between({"arm": {"method": method}})))
    assert found == {
        "E-DATA-ASSIGN-DRAWN",
    }
    assert "E-DATA-ASSIGN-METHOD" not in found

    c = Collector()
    _check_assign({}, {"assign": {"arm": {"method": method}}}, None, c)
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-DRAWN"]
    assert c.findings[0].path == "data.units.assign.arm.method"
    # The wording, not just the code: `E-DATA-ASSIGN-METHOD`'s out-of-enum branch
    # also formats `is {method!r}, which is not...`, so a test asserting the code
    # alone would pass with the `elif method in DRAWN_ASSIGN_METHODS` branch
    # deleted and the out-of-enum branch mutated to swallow it. `by_attribute`,
    # the supported alternative, is what discriminates this message from that
    # one.
    assert "by_attribute" in c.findings[0].message
    assert method in c.findings[0].message


def test_a_partial_ratio_is_refused(write_config):
    """§ Allocation: "a partial mapping is rejected rather than defaulted, since
    'one entry per level' is checkable and 'the levels I left out get the
    average' is a rule nobody should have to infer." Two levels, one entry.

    `ratio` only means anything for a method that draws, so this is checked
    under `random`/`blocked` — `E-DATA-ASSIGN-DRAWN` fires beside it, and the
    exact-set assertion is what keeps this test's teeth once task 14 retires
    that code and the set shrinks to just `E-DATA-ASSIGN-RATIO`."""
    found = _error_codes(
        write_config(_between({"arm": {"method": "random", "ratio": {"control": 1}}}))
    )
    assert found == {"E-DATA-ASSIGN-DRAWN", "E-DATA-ASSIGN-RATIO"}

    c = Collector()
    _check_assign(
        {"sweep": {"groups": _ARM_AXIS}},
        {
            "allocation": "between",
            "assign": {"arm": {"method": "random", "ratio": {"control": 1}}},
        },
        None,
        c,
    )
    assert {f.code for f in c.findings} == {"E-DATA-ASSIGN-DRAWN", "E-DATA-ASSIGN-RATIO"}
    ratio_finding = next(f for f in c.findings if f.code == "E-DATA-ASSIGN-RATIO")
    assert ratio_finding.path == "data.units.assign.arm.ratio"
    # "has key 'control'", not "keys" and not the declared-levels pair — the
    # declared `ratio` has one entry, and a mutation swapping its keys for the
    # axis's `levels` in the message would still contain 'control' and 'arm',
    # so the singular-key substring is what discriminates the two.
    assert "has key 'control';" in ratio_finding.message
    assert "'arm'" in ratio_finding.message
    assert "'treatment'" in ratio_finding.message


def test_a_ratio_naming_an_undeclared_level_is_refused(write_config):
    """`ratio: {control: 1, f: 2}` against levels [control, treatment]."""
    found = _error_codes(
        write_config(
            _between({"arm": {"method": "blocked", "ratio": {"control": 1, "f": 2}}})
        )
    )
    assert found == {"E-DATA-ASSIGN-DRAWN", "E-DATA-ASSIGN-RATIO"}

    c = Collector()
    _check_assign(
        {"sweep": {"groups": _ARM_AXIS}},
        {
            "allocation": "between",
            "assign": {"arm": {"method": "blocked", "ratio": {"control": 1, "f": 2}}},
        },
        None,
        c,
    )
    assert {f.code for f in c.findings} == {"E-DATA-ASSIGN-DRAWN", "E-DATA-ASSIGN-RATIO"}
    ratio_finding = next(f for f in c.findings if f.code == "E-DATA-ASSIGN-RATIO")
    assert ratio_finding.path == "data.units.assign.arm.ratio"
    assert "'f'" in ratio_finding.message


def test_a_ratio_with_every_level_plus_an_extra_key_is_refused(write_config):
    """The set-inequality direction `test_a_ratio_naming_an_undeclared_level_is_refused`
    cannot isolate on its own: `{control: 1, f: 2}` is simultaneously missing
    `treatment` *and* naming an undeclared key, so a check reading only "every
    declared level has an entry" (`not set(levels) <= set(ratio)`, missing the
    other half of the promised set-equality) passes that test just as well as
    the real `set(ratio) != set(levels)` does. `{control: 1, treatment: 1, f: 2}`
    is a strict superset of the declared levels — every level present, plus one
    that isn't — so it isolates the direction the other two tests can't: refused
    only if the check also catches an extra key beside a complete level set."""
    found = _error_codes(
        write_config(
            _between(
                {
                    "arm": {
                        "method": "random",
                        "ratio": {"control": 1, "treatment": 1, "f": 2},
                    }
                }
            )
        )
    )
    assert found == {"E-DATA-ASSIGN-DRAWN", "E-DATA-ASSIGN-RATIO"}

    c = Collector()
    _check_assign(
        {"sweep": {"groups": _ARM_AXIS}},
        {
            "allocation": "between",
            "assign": {
                "arm": {
                    "method": "random",
                    "ratio": {"control": 1, "treatment": 1, "f": 2},
                }
            },
        },
        None,
        c,
    )
    assert {f.code for f in c.findings} == {"E-DATA-ASSIGN-DRAWN", "E-DATA-ASSIGN-RATIO"}
    ratio_finding = next(f for f in c.findings if f.code == "E-DATA-ASSIGN-RATIO")
    assert ratio_finding.path == "data.units.assign.arm.ratio"
    assert "'f'" in ratio_finding.message


def test_a_non_empty_ratio_under_by_attribute_is_refused():
    """The draw didn't happen, so the proportion describes nothing. § Allocation:
    "Under `method: by_attribute` a `ratio` describes a draw that didn't happen,
    so `validate` rejects a non-empty one instead of recording a proportion the
    data may not honour." A full, correctly-keyed ratio still earns this — the
    fault is presence under this method, not shape."""
    c = Collector()
    _check_assign(
        {},
        {
            "attributes": ["arm"],
            "assign": {
                "arm": {
                    "method": "by_attribute",
                    "ratio": {"control": 1, "treatment": 1},
                }
            },
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-NO-DRAW"]
    assert c.findings[0].path == "data.units.assign.arm.ratio"
    assert "by_attribute" in c.findings[0].message


def test_an_empty_ratio_is_equal_allocation_and_is_accepted():
    """The control, and it must report: `{}` is what `init` writes and what most
    designs carry, so a check that refused it would fire on the common case.
    Assert the exact finding set, not an absence."""
    c = Collector()
    _check_assign(
        {},
        {
            "attributes": ["arm"],
            "assign": {"arm": {"method": "by_attribute", "ratio": {}}},
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == []


def test_a_full_ratio_under_a_drawn_method_is_accepted():
    """The second control. Under this build the config still reports
    `E-DATA-ASSIGN-DRAWN` — assert that exact set, so the test keeps its teeth
    when task 14 retires that code and the set becomes empty."""
    c = Collector()
    _check_assign(
        {"sweep": {"groups": _ARM_AXIS}},
        {
            "allocation": "between",
            "assign": {
                "arm": {"method": "random", "ratio": {"control": 1, "treatment": 1}}
            },
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-DRAWN"]


def test_a_non_empty_stratify_by_under_by_attribute_is_refused():
    """§ Allocation: "The same is true of `assign.<axis>.stratify_by`: under
    `method: by_attribute` it would describe how a draw was balanced when none
    was — the same fault — so `validate` rejects a non-empty one there too."
    Task 3's ruling: this task owns both halves of that sentence, not just
    `ratio`."""
    c = Collector()
    _check_assign(
        {},
        {
            "attributes": ["arm"],
            "assign": {"arm": {"method": "by_attribute", "stratify_by": ["site"]}},
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-NO-DRAW"]
    assert c.findings[0].path == "data.units.assign.arm.stratify_by"
    assert "by_attribute" in c.findings[0].message


def test_an_empty_stratify_by_under_by_attribute_is_accepted():
    """The control for the `stratify_by` half: an empty list changes no
    behavior and must not be refused."""
    c = Collector()
    _check_assign(
        {},
        {
            "attributes": ["arm"],
            "assign": {"arm": {"method": "by_attribute", "stratify_by": []}},
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == []


def test_a_wrong_typed_ratio_under_by_attribute_is_refused():
    """`ratio` is not an `envelope.py` `LEAF_TYPES` leaf and task 4's key-closure
    check closes axis-block *names*, not the *types* of their values, so a bare
    `ratio: 3` — a routine YAML slip for a mapping — is read by nothing else in
    `src/`. `E-DATA-ASSIGN-NO-DRAW`'s fault is presence, not shape, so this is
    absorbed under the same code as a well-formed non-empty `ratio` rather than
    left silent or given a code of its own."""
    c = Collector()
    _check_assign(
        {},
        {
            "attributes": ["arm"],
            "assign": {"arm": {"method": "by_attribute", "ratio": 3}},
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-NO-DRAW"]
    assert c.findings[0].path == "data.units.assign.arm.ratio"
    assert "3" in c.findings[0].message


def test_a_wrong_typed_stratify_by_under_by_attribute_is_refused():
    """The `stratify_by` half of the same absorption: a bare `stratify_by: site`
    — the list form left off — where nothing else in `src/` reads
    `assign.<axis>.stratify_by` at all, wrong-typed or not."""
    c = Collector()
    _check_assign(
        {},
        {
            "attributes": ["arm"],
            "assign": {"arm": {"method": "by_attribute", "stratify_by": "site"}},
        },
        None,
        c,
    )
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-NO-DRAW"]
    assert c.findings[0].path == "data.units.assign.arm.stratify_by"
    assert "site" in c.findings[0].message


def test_an_assignment_declaring_no_method_is_refused(write_config):
    """§ Validation's example exactly: a block declaring `stratify_by` and no
    `method`. Which of the block's other fields are read follows from the
    discriminator, so a block without one describes no assignment."""
    assert _error_codes(
        write_config(_between({"arm": {"stratify_by": ["site"]}}))
    ) == {
        "E-DATA-ASSIGN-METHOD",
    }

    c = Collector()
    _check_assign({}, {"assign": {"arm": {"stratify_by": ["site"]}}}, None, c)
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-METHOD"]
    assert c.findings[0].path == "data.units.assign.arm.method"
    # The wording, not just the code: an absent `method` and a misspelled one
    # share an identifier, so a test asserting the code alone passes with the
    # presence branch deleted — `None` is not in the enum either, and the
    # out-of-enum branch would catch it saying the wrong thing.
    assert "not declared" in c.findings[0].message


def test_an_assignment_method_outside_the_enum_is_refused(write_config):
    """§ Validation's other example, `by_column`. A well-formed name that is not
    one of the three is the branch a presence check alone would let through."""
    assert _error_codes(
        write_config(_between({"arm": {"method": "by_column"}}))
    ) == {
        "E-DATA-ASSIGN-METHOD",
    }

    c = Collector()
    _check_assign({}, {"assign": {"arm": {"method": "by_column"}}}, None, c)
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-METHOD"]
    assert "by_column" in c.findings[0].message


def test_a_misspelled_key_inside_an_assign_block_is_reported(write_config):
    """`stratifyy_by` is silently ignored today: `envelope.py` types
    `data.units.assign` a bare `dict` and none of its children, so nothing
    closes an axis block. The control is the correctly spelled key, which must
    NOT be reported — an allowlist that rejects everything passes the first
    assertion and fails the design."""
    units = {
        "allocation": "between",
        "assign": {"arm": {"method": "by_attribute", "stratifyy_by": ["site"]}},
    }
    assert "E-CONFIG-KEY-UNKNOWN" in codes(write_config({"data.units": units}))
    ok = {
        "allocation": "between",
        "assign": {"arm": {"method": "by_attribute", "from": "arm"}},
    }
    assert "E-CONFIG-KEY-UNKNOWN" not in codes(write_config({"data.units": ok}))


@pytest.mark.parametrize(
    "key,value,typo",
    [
        ("method", "by_attribute", "methdo"),
        ("from", "arm", "form"),
        ("ratio", {"treatment": 1, "control": 1}, "ratios"),
        ("block_size", "auto", "blocksize"),
        ("stratify_by", ["site"], "stratifyy_by"),
        ("seed", "auto", "seeds"),
    ],
)
def test_each_assign_axis_key_is_closed_key_by_key(write_config, key, value, typo):
    """`ASSIGN_AXIS_KEYS` is a closed *set*, not a list with some decorative
    entries — a key removed from it silently by a future edit would only be
    caught if some test pins that exact key down. `stratify_by` above is one
    such case, but the other five had no case of their own before this test:
    coverage for them rested on incidental hits in unrelated tests (`ratio`,
    `block_size`, `seed`) or on nothing at all. Mirrors the enum-style
    parametrization `ASSIGN_METHODS`/`ALLOCATION_MODES` get elsewhere in this
    file — one case per legal value, correctly spelled and misspelled."""
    ok = {"allocation": "between", "assign": {"arm": {key: value}}}
    assert "E-CONFIG-KEY-UNKNOWN" not in codes(write_config({"data.units": ok}))

    bad = {"allocation": "between", "assign": {"arm": {typo: value}}}
    bad_path = write_config({"data.units": bad})
    c = Collector()
    validate_config(bad_path, c)
    fields = [f.path for f in c.findings if f.code == "E-CONFIG-KEY-UNKNOWN"]
    assert f"data.units.assign.arm.{typo}" in fields


@pytest.mark.parametrize(
    "assign",
    [
        {"arm": "random"},                    # the block itself is not a block
        {"arm": {"method": 3}},               # a non-string discriminator
        {"arm": {"method": ["random"]}},      # a structural one
    ],
)
def test_a_malformed_assignment_block_reports_rather_than_crashes(assign):
    """`validate` collects and never raises, and `envelope.py` types
    `data.units.assign` itself but none of its children — an axis name is not a
    key any fixed dotted path could ever name — so nothing else speaks for
    these."""
    c = Collector()
    _check_assign({}, {"assign": assign}, None, c)
    assert [f.code for f in c.findings] == ["E-DATA-ASSIGN-METHOD"]


@pytest.mark.parametrize(
    "doc,units",
    [
        ({"sweep": "grid"}, {"allocation": "between"}),
        ({"sweep": {"groups": "arm"}}, {"allocation": "between"}),
        ({"sweep": {"groups": [{"by": 123}]}}, {"allocation": "between", "assign": {}}),
        ({}, {"allocation": 3, "assign": "random"}),
        ({}, {"assign": []}),
    ],
)
def test_the_assignment_checks_are_total_over_malformed_declarations(doc, units):
    """Every one of these has its own reporter — `E-CONFIG-SHAPE` for a
    string `sweep`, `E-CONFIG-TYPE` for a non-mapping `assign` — and none of
    them may become a traceback here. The first three report the arms fault
    honestly, since an unreadable axis is an axis nothing can assign."""
    c = Collector()
    _check_assign(doc, units, None, c)
    assert all(f.code.startswith("E-DATA-") for f in c.findings)
