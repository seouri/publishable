# tests/test_validate.py
from pathlib import Path

import pytest
import yaml
from tests.conftest import write_experiment_module

from publishable.diagnostics import Collector
from publishable.validate import validate_config


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


_DELETE = object()


def codes(path: Path) -> set[str]:
    c = Collector()
    validate_config(path, c)
    return {f.code for f in c.findings}


def messages_by_code(path: Path) -> dict[str, str]:
    c = Collector()
    validate_config(path, c)
    return {f.code: f.message for f in c.findings}


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


def test_fold_stratify_by_is_refused_through_validate(write_config):
    assert "E-REPL-FOLD-STRATIFY-UNSUPPORTED" in codes(
        write_config(
            {"replication": {"repeats": [{"kind": "fold", "k": 5, "stratify_by": "site"}]}}
        )
    )


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

    def _boom(doc, digest, unit_count=None):
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
    """`paired`/`ablate`/`sample`/`groups` are refused by `_check_unimplemented` under
    their own identifiers; `_check_sweep` must not double-report them as unknown."""
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


def test_the_budget_check_fires_for_leave_one_out_against_the_real_roster(
    write_config, tmp_path
):
    """Leave-one-out is the single design `W-EXEC-BUDGET` matters most for
    (`reference.md` § Sweeps and repeats) — and it was the one design that could
    not produce the warning, because `_repeat_total` returned `None` on any
    string count while `_check_replication` had already been threaded a real
    `unit_count`. A 60-unit roster under `k: all` is 60 executions against a
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
    _check_replication(doc, ThreeRepeats(), resolved, unit_count=2)
    assert "W-REPL-FLOOR" in {f.code for f in resolved.findings}

    # ...and still silent when the roster genuinely could not resolve.
    unresolved = Collector()
    _check_replication(doc, ThreeRepeats(), unresolved, unit_count=None)
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


@pytest.mark.parametrize(
    "mode,value,code",
    [
        ("paired", [{"analysis.method": "pearson"}], "E-SWEEP-PAIRED-UNSUPPORTED"),
        ("ablate", {"from": "baseline", "remove": ["a.b"]}, "E-SWEEP-ABLATE-UNSUPPORTED"),
        ("sample", {"n": 40, "ranges": {}}, "E-SWEEP-SAMPLE-UNSUPPORTED"),
        ("groups", [{"by": "arm", "levels": ["a", "b"]}], "E-SWEEP-GROUPS-UNSUPPORTED"),
    ],
)
def test_each_unimplemented_mode_is_refused_on_its_own(write_config, mode, value, code):
    """`paired`, `ablate`, `sample`, and `groups` each get their own refusal now that
    the old blanket sweep refusal is retired — otherwise each would fall through
    into silence the moment `baseline`/`grid` stopped covering the whole block."""
    assert code in codes(write_config({"sweep": {mode: value}}))


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


def test_every_sweep_refusal_message_defers_rather_than_scolds(write_config):
    for mode, value, code in [
        ("paired", [{"a.b": 1}], "E-SWEEP-PAIRED-UNSUPPORTED"),
        ("ablate", {"from": "baseline"}, "E-SWEEP-ABLATE-UNSUPPORTED"),
        ("sample", {"n": 1}, "E-SWEEP-SAMPLE-UNSUPPORTED"),
        ("groups", [{"by": "arm"}], "E-SWEEP-GROUPS-UNSUPPORTED"),
    ]:
        c = Collector()
        validate_config(write_config({"sweep": {mode: value}}), c)
        message = next(f.message for f in c.findings if f.code == code)
        assert "later slice" in message, f"{code} must defer, not scold"


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


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("allocation", "between", "E-DATA-ALLOCATION-UNSUPPORTED"),
        ("assign", {"arm": {"method": "random"}}, "E-DATA-ASSIGN-UNSUPPORTED"),
        ("cluster_by", "site", "E-DATA-CLUSTER-UNSUPPORTED"),
        ("weight_by", "sampling_weight", "E-DATA-WEIGHT-UNSUPPORTED"),
        ("measurements", {"by": "read_id"}, "E-DATA-MEASUREMENTS-UNSUPPORTED"),
        ("holdout", {"method": "random", "frac": 0.2}, "E-DATA-HOLDOUT-UNSUPPORTED"),
    ],
)
def test_each_unimplemented_units_subfield_is_refused_on_its_own(write_config, field, value, code):
    units = {"from": "index.csv", "key": "patient_id", field: value}
    assert code in codes(write_config({"data.units": units}))


def test_allocation_within_is_accepted_because_it_is_a_no_op_here(write_config):
    units = {"from": "index.csv", "key": "patient_id", "allocation": "within"}
    assert "E-DATA-ALLOCATION-UNSUPPORTED" not in codes(write_config({"data.units": units}))


def test_a_resolver_source_is_refused_until_plugins_exist(write_config):
    units = {"from": {"resolver": "plate_wells"}, "key": "well"}
    assert "E-DATA-RESOLVER-UNSUPPORTED" in codes(write_config({"data.units": units}))


@pytest.mark.parametrize(
    "units",
    [
        {"from": {"resolver": "plate_wells"}, "key": "well"},
        {"from": "index.csv", "key": "patient_id", "allocation": "between"},
        {"from": "index.csv", "key": "patient_id", "assign": {"arm": {"method": "random"}}},
        {"from": "index.csv", "key": "patient_id", "cluster_by": "site"},
        {"from": "index.csv", "key": "patient_id", "weight_by": "sampling_weight"},
        {"from": "index.csv", "key": "patient_id", "measurements": {"by": "read_id"}},
        {"from": "index.csv", "key": "patient_id", "holdout": {"method": "random", "frac": 0.2}},
    ],
)
def test_every_unsupported_message_defers_rather_than_scolds(write_config, units):
    """The `-UNSUPPORTED` family exists so a refusal reads as 'not built yet', not as
    'your config is wrong'. Every message in this family must say so explicitly, or a
    user has no way to tell a refusal from a validation error."""
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


def test_declared_report_by_is_refused(write_config):
    assert "E-STATS-REPORTBY-UNSUPPORTED" in codes(
        write_config({"statistics": {"report_by": ["sex"]}})
    )


def test_a_declared_hypothesis_is_refused(write_config):
    assert "E-HYPOTHESIS-UNSUPPORTED" in codes(
        write_config({"hypotheses": [{"id": "h1", "metric": "r", "direction": "greater"}]})
    )


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
    `SWEPT_VALUE_PATTERN` on the space, and the baseline still fixes every grid
    axis, so `E-SWEEP-BASELINE-PARTIAL` does not fire either. Both directions are
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
    assert "E-SWEEP-BASELINE-PARTIAL" not in found


def test_a_baseline_that_leaves_a_grid_axis_free_is_refused(write_config):
    """`reference.md`:1415-1422 requires one baseline condition per cell of the
    unfixed axes; `expand` emits exactly one. Refused rather than diverging."""
    found = messages_by_code(
        write_config(
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
    )
    assert "E-SWEEP-BASELINE-PARTIAL" in found
    assert "analysis.min_samples" in found["E-SWEEP-BASELINE-PARTIAL"]
    assert "not implemented in this build" in found["E-SWEEP-BASELINE-PARTIAL"]


def test_a_baseline_fixing_every_axis_is_supported(write_config):
    """The row the slice's worked example uses, and it must keep working."""
    found = codes(
        write_config(
            {
                "sweep": {
                    "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
                    "grid": {"analysis.min_samples": [10, 20]},
                }
            }
        )
    )
    assert "E-SWEEP-BASELINE-PARTIAL" not in found


def test_a_bare_baseline_with_no_grid_is_supported(write_config):
    """No grid means no unfixed axis, so the bare-baseline level stays legal."""
    found = codes(write_config({"sweep": {"baseline": {"analysis.method": "pearson"}}}))
    assert "E-SWEEP-BASELINE-PARTIAL" not in found


def test_an_empty_baseline_beside_a_grid_is_not_a_partial_baseline(write_config):
    """`baseline: {}` declares nothing and yields no baseline condition; "present
    but empty is not a declaration" is this repo's convention elsewhere too."""
    found = codes(
        write_config(
            {"sweep": {"baseline": {}, "grid": {"analysis.method": ["spearman", "kendall"]}}}
        )
    )
    assert "E-SWEEP-BASELINE-PARTIAL" not in found


def test_a_list_grid_is_a_diagnostic_not_a_traceback(write_config):
    """`_check_sweep` calls `grid.items()`; without the shape guard this escaped
    `main`'s handler as `AttributeError: 'list' object has no attribute 'items'`."""
    found = codes(write_config({"sweep": {"grid": ["analysis.method"]}}))
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
                "statistics": {
                    "contrasts": [{"id": "x", "of": "nosuch", "against": "nosuch"}]
                },
            }
        )
    )
    assert "E-STATS-CONTRAST-UNKNOWN" in found
    assert "E-STATS-CONTRAST-SAME-SIDES" not in found


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
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {"contrasts": {"id": "x", "of": "baseline"}},
            }
        )
    )
    assert "E-STATS-CONTRAST-SHAPE" in found


def test_a_contrast_without_an_id_is_refused(write_config):
    """`id` names the entry in `results.contrasts` and in a hypothesis. Missing,
    it reached the record as the literal string `'None'`, and two such entries
    collided under one name."""
    found = codes(
        write_config(
            {
                "sweep": _TWO_CONDITIONS,
                "statistics": {
                    "contrasts": [{"of": "method=spearman", "against": "baseline"}]
                },
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
    and raises on a bool or an int, and the family count in `_check_sweep` reads
    the block before `_check_contrasts` refuses its shape. `validate.py`
    collects findings and never raises, so this has to come back as a
    diagnostic — the assertion is that `validate_config` returns at all."""
    for block in (5, True, "method=spearman"):
        found = codes(
            write_config({"sweep": _TWO_CONDITIONS, "statistics": {"contrasts": block}})
        )
        assert "E-STATS-CONTRAST-SHAPE" in found


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
    found = codes(
        write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "fdr_bh"}})
    )
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
