"""H9c — `reproduce`. Fixture S, the operand discrimination (design § 9).

Every literal here is either computed in the test or read back out of the
artifact the fixture built. The two `run`-driven fixtures come from
`tests.test_cli`'s `run_a_project`, the one end-to-end driver this suite has —
re-inventing the scaffold-and-commit dance is how a fixture drifts from what
`run` actually writes.
"""

from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project

from publishable.diagnostics import Collector
from publishable.reproduce import ConfigOperand, Record, classify_operand
from publishable.study import study_add, study_new


def _a_run(tmp_path: Path) -> dict:
    return run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=10)


def _classify(path: Path, credentials: dict[str, str] | None = None):
    """Classify, and hand back the collector so a test can assert on findings.

    The collector is built fresh per call and carries credentials when the test
    gives it any — design correction 21: `main`'s `except PublishableError`
    handler applies NO redaction pass, so a refusal that travelled as an
    exception would reach a reader un-redacted. Every arm below therefore
    asserts on `c.findings`, and the arms assert that nothing was RAISED by
    reaching that assertion at all.
    """
    c = Collector(credentials=dict(credentials or {}))
    return classify_operand(path, c), c


def _codes(c: Collector) -> list[str]:
    return [f.code for f in c.findings]


def _messages(c: Collector) -> str:
    return "\n".join(f.message for f in c.findings)


# --- The honouring, first. Three accepted forms. ---------------------------
# `Testing the refusal, never the honouring` is a shape this repo has paid for
# more than once, and a discrimination test made only of refusals cannot tell
# a working reader from one that refuses everything.


def test_a_run_directorys_own_run_yaml_is_accepted_as_a_record(tmp_path: Path):
    doc = _a_run(tmp_path)
    operand, c = _classify(doc["run_dir"] / "run.yaml")
    assert isinstance(operand, Record)
    assert c.findings == []
    assert (
        operand.doc["run_id"] == yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())["run_id"]
    )
    assert operand.path == doc["run_dir"] / "run.yaml"


def test_a_bundle_member_named_main_run_yaml_is_accepted_as_a_record(tmp_path: Path):
    """Ruling Y's cost-if-wrong, as a test rather than a sentence.

    A bundle member is `main.run.yaml`. This is the arm the basename mutation
    (`endswith("run.yaml")`) fails, and it is the form a reader holding a
    published bundle — the case `study` exists to serve — actually has.
    """
    doc = _a_run(tmp_path)
    bundle = tmp_path / "study"
    study_new(bundle, "Fixture S")
    study_add(bundle, doc["run_dir"] / "run.yaml", "main")
    member = bundle / "main.run.yaml"
    assert member.name != "run.yaml", member.name

    operand, c = _classify(member)
    assert isinstance(operand, Record)
    assert c.findings == []
    assert operand.doc["run_id"] == yaml.safe_load(member.read_text())["run_id"]


def test_a_config_file_is_accepted_as_a_config_operand(tmp_path: Path):
    doc = _a_run(tmp_path)
    operand, c = _classify(doc["cfg"])
    assert isinstance(operand, ConfigOperand)
    assert c.findings == []
    assert operand.path == doc["cfg"]


# --- Fixture S: the five refusals. ----------------------------------------


def test_fixture_s_arm_1_a_run_directory_is_refused_and_names_its_run_yaml(tmp_path: Path):
    """Arm 1. `resume` takes a directory; `reproduce` takes the file in it, and
    the message supplies the component the user is missing."""
    doc = _a_run(tmp_path)
    operand, c = _classify(doc["run_dir"])
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-OPERAND"]
    assert str(doc["run_dir"] / "run.yaml") in _messages(c)


def test_fixture_s_arm_2_a_study_yaml_is_refused_listing_both_members(tmp_path: Path):
    """Arm 2. TWO members, on purpose: a one-member bundle cannot distinguish
    *lists the members* from *names the first*, so the count-instead-of-names
    mutation would pass against one.

    The two names are asserted individually AND the count `2` is asserted
    absent from the message, because a message reading "2 members" would
    otherwise satisfy an `in` check on neither name.
    """
    first = _a_run(tmp_path / "a")
    second = _a_run(tmp_path / "b")
    bundle = tmp_path / "study"
    study_new(bundle, "Fixture S")
    study_add(bundle, first["run_dir"] / "run.yaml", "main")
    study_add(bundle, second["run_dir"] / "run.yaml", "sensitivity")
    assert sorted(yaml.safe_load((bundle / "study.yaml").read_text())["runs"]) == [
        "main",
        "sensitivity",
    ]

    operand, c = _classify(bundle / "study.yaml")
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-BUNDLE"]
    message = _messages(c)
    assert "`main.run.yaml`" in message, message
    assert "`sensitivity.run.yaml`" in message, message
    assert "2" not in message, message


def test_fixture_s_arm_2b_a_freshly_created_empty_bundle_says_it_holds_none(tmp_path: Path):
    """Arm 2's other end, which the two-member arm cannot reach: `study new`
    writes `runs: {}`, and an empty list rendered as a list reads as naming
    nothing at all rather than as an answer."""
    bundle = tmp_path / "study"
    study_new(bundle, "Fixture S")
    operand, c = _classify(bundle / "study.yaml")
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-BUNDLE"]
    assert "holds no runs yet" in _messages(c)


def test_fixture_s_arm_3_a_record_with_run_id_deleted_is_not_read_as_a_config(tmp_path: Path):
    """Arm 3, and it is the arm the *read a `run_id`-less mapping as a config*
    mutation fails.

    The file keeps `provenance` and `results` and loses only `run_id`, so the
    two readings genuinely differ: refused as an edited record, or read as a
    config. It carries no `experiment_type`, so the message is what separates
    them — a reader sent to "this is not a config" would go and look at the
    wrong file.
    """
    doc = _a_run(tmp_path)
    record = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert "provenance" in record and "results" in record
    del record["run_id"]
    edited = tmp_path / "edited.run.yaml"
    edited.write_text(yaml.safe_dump(record, sort_keys=False))

    operand, c = _classify(edited)
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-OPERAND"]
    message = _messages(c)
    assert "no `run_id`" in message, message
    assert "edited or truncated" in message, message


def test_fixture_s_arm_4_a_yaml_list_is_refused_as_an_operand(tmp_path: Path):
    path = tmp_path / "list.yaml"
    path.write_text("- one\n- two\n")
    operand, c = _classify(path)
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-OPERAND"]
    assert "list, not a mapping" in _messages(c)


def test_fixture_s_arm_5_a_missing_path_is_e_io_failed(tmp_path: Path):
    """Arm 5. `E-IO-FAILED`, `diff`'s and `resume`'s precedent, and NOT
    `read_record_file`'s `E-UPSTREAM-RECORD-MISSING`: at this point nothing has
    established that the operand was meant to be a record at all."""
    operand, c = _classify(tmp_path / "nowhere.yaml")
    assert operand is None
    assert _codes(c) == ["E-IO-FAILED"]


# --- Two properties the five arms do not cover on their own. ---------------


def test_a_record_whose_schema_version_this_build_cannot_read_keeps_its_own_code(tmp_path: Path):
    """`read_record_file`'s refusals are re-reported through the collector WITH
    THEIR OWN CODES, rather than being flattened into
    `E-REPRODUCE-OPERAND` — H9c is that reader's fifth caller and mints no
    refusal of its own for the parse."""
    doc = _a_run(tmp_path)
    record = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    record["schema_version"] = "9.9"
    path = tmp_path / "future.run.yaml"
    path.write_text(yaml.safe_dump(record, sort_keys=False))

    operand, c = _classify(path)
    assert operand is None
    assert _codes(c) == ["E-UPSTREAM-RECORD-VERSION"]


def test_a_refusal_is_rendered_through_a_credential_bearing_collector(tmp_path: Path):
    """The redaction pass is `Collector.render`'s, and it is reachable here
    only because the refusal is APPENDED rather than raised — `main`'s
    `except PublishableError` handler applies no redaction pass at all
    (measured by H9b), so a raise would print this value verbatim.

    The credential reaches the message through the YAML parse error, which
    quotes the offending line. That is a real route, not a contrivance: a
    `.env`-style value pasted into a config is exactly how a secret lands in a
    file core is asked to read.
    """
    secret = "sk-h9c-task2-not-a-real-key"
    path = tmp_path / "broken.yaml"
    # The secret must sit ON the offending line, not merely in the file:
    # `yaml`'s error quotes one line, and the first draft of this fixture put
    # the secret on line 1 with the fault on line 2 — its own control caught
    # that, which is what a fixture-as-a-claim assertion is for.
    path.write_text(f"token: {secret}: trailing\n")

    operand, c = _classify(path, credentials={"H9C_TOKEN": secret})
    assert operand is None
    assert _codes(c) == ["E-IO-FAILED"]
    assert secret in _messages(c), "the fixture must actually carry the value it redacts"
    rendered = c.render()
    assert secret not in rendered, rendered
    assert "<redacted:H9C_TOKEN>" in rendered, rendered


@pytest.mark.parametrize(
    "text",
    ["", "null\n", "42\n", "a string\n"],
)
def test_a_document_that_is_not_a_mapping_never_raises(tmp_path: Path, text: str):
    """Reaching the assertion at all is the claim: nothing in this module
    raises into `main`, including the empty-file case, where `safe_load`
    returns `None` rather than failing."""
    path = tmp_path / "odd.yaml"
    path.write_text(text)
    operand, c = _classify(path)
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-OPERAND"]
