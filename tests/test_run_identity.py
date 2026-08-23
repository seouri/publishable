import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from publishable import ContractError
from publishable.run_identity import (
    IDENTITY_FILE,
    RunLock,
    allocate_run_dir,
    config_path_for,
    identity_document,
    point_latest,
    read_identity,
    read_repo_root,
)

WHEN = datetime(2026, 8, 8, 14, 2, 11, tzinfo=UTC)
HASH = "sha256:8e21ab3cafe0000000000000000000000000000000000000000000000000000"


def test_the_id_is_timestamp_then_short_code_hash(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    assert run_dir.name == "run_2026-08-08T14-02-11Z_8e21ab3"
    assert run_dir.is_dir()


def test_a_collision_is_resolved_by_suffix_not_by_precision(tmp_path: Path):
    first = allocate_run_dir(tmp_path, HASH, WHEN)
    second = allocate_run_dir(tmp_path, HASH, WHEN)
    third = allocate_run_dir(tmp_path, HASH, WHEN)
    assert second.name == first.name + "_b"
    assert third.name == first.name + "_c"


def test_latest_points_at_the_real_id(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    point_latest(tmp_path, run_dir)
    latest = tmp_path / "latest"
    resolved = (
        latest.resolve()
        if latest.is_symlink()
        else tmp_path / (tmp_path / "latest.txt").read_text().strip()
    )
    assert resolved.name == run_dir.name


def test_the_lock_records_who_holds_it_and_is_released(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):
        assert (run_dir / "lock").is_file()
        assert "pid" in (run_dir / "lock").read_text()
    assert not (run_dir / "lock").exists()


def test_a_held_lock_is_reported_rather_than_assumed_dead(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):
        with pytest.raises(ContractError) as e:
            with RunLock(run_dir):
                pass
        assert e.value.code == "E-RUN-LOCKED"


def _sole_pointer_target(tmp_path: Path) -> str:
    """Assert exactly one pointer form exists and return the run id it names."""
    link = tmp_path / "latest"
    text = tmp_path / "latest.txt"
    link_there = link.is_symlink() or link.exists()
    text_there = text.exists()
    assert link_there != text_there, "exactly one pointer form must exist"
    if link_there:
        return link.resolve().name
    return text.read_text().strip()


def test_a_fallback_run_followed_by_a_symlink_run_leaves_one_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    first = allocate_run_dir(tmp_path, HASH, WHEN)
    second = allocate_run_dir(tmp_path, HASH, WHEN)

    real_symlink_to = Path.symlink_to

    def failing_symlink_to(self: Path, *args: object, **kwargs: object) -> None:
        raise OSError("symlinks unavailable")

    monkeypatch.setattr(Path, "symlink_to", failing_symlink_to)
    point_latest(tmp_path, first)
    assert _sole_pointer_target(tmp_path) == first.name

    monkeypatch.setattr(Path, "symlink_to", real_symlink_to)
    point_latest(tmp_path, second)
    assert _sole_pointer_target(tmp_path) == second.name


def test_a_symlink_run_followed_by_a_fallback_run_leaves_one_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    first = allocate_run_dir(tmp_path, HASH, WHEN)
    second = allocate_run_dir(tmp_path, HASH, WHEN)

    point_latest(tmp_path, first)
    assert _sole_pointer_target(tmp_path) == first.name

    def failing_symlink_to(self: Path, *args: object, **kwargs: object) -> None:
        raise OSError("symlinks unavailable")

    monkeypatch.setattr(Path, "symlink_to", failing_symlink_to)
    point_latest(tmp_path, second)
    assert _sole_pointer_target(tmp_path) == second.name


def test_a_held_locks_message_survives_a_vanished_lock_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):

        def unreadable(self: Path, *args: object, **kwargs: object) -> str:
            raise OSError("lock file vanished mid-read")

        monkeypatch.setattr(Path, "read_text", unreadable)
        with pytest.raises(ContractError) as e:
            with RunLock(run_dir):
                pass
        assert e.value.code == "E-RUN-LOCKED"


# --- H9b task 2: `identity.json`, what a run makes durable before it runs ---


def _document(**overrides: object) -> dict[str, object]:
    """A well-formed identity document, `overrides` applied after."""
    document = identity_document(
        code_hash=HASH,
        parameters_hash="sha256:1a2b" + "0" * 60,
        uv_lock_hash=None,
        config_path_rel="configs/cohort/config.yaml",
        draft=False,
    )
    document.update(overrides)
    return document


def test_the_document_is_five_keys_in_one_order():
    document = identity_document(
        code_hash=HASH,
        parameters_hash="sha256:1a2b",
        uv_lock_hash="sha256:6b1f",
        config_path_rel="configs/cohort/config.yaml",
        draft=True,
    )
    assert list(document) == [
        "code_hash",
        "parameters_hash",
        "uv_lock_hash",
        "config_path",
        "draft",
    ]
    assert document["config_path"] == "configs/cohort/config.yaml"
    assert document["draft"] is True
    # `input_manifest_hash` is deliberately absent: `manifest/input.json` is
    # itself the operand, so its digest would have no reader.
    assert "input_manifest_hash" not in document


def _strict_loads(text: str) -> object:
    """`json.loads` that REFUSES the three tokens `json.dumps` emits for
    non-finite floats.

    The plan's correction 22 measured that `json.dumps` emits bare `NaN` and
    `Infinity` — neither valid RFC 8259 — and that `coerce_scalars` passes a
    non-finite float through, so "serializable by invariant" is false as a
    ground. A plain `json.loads` ACCEPTS those tokens, so a round trip
    asserted with it could not tell a clean document from one carrying them:
    this reader can fail, which is what makes the round trip below a pin.
    """

    def reject(name: str) -> object:
        raise AssertionError(f"non-finite JSON token {name!r} in the document")

    return json.loads(text, parse_constant=reject)


def test_the_document_round_trips_through_a_reader_that_can_fail(tmp_path: Path):
    document = _document(uv_lock_hash="sha256:6b1f")
    text = json.dumps(document, indent=2)
    assert _strict_loads(text) == document
    # The reader really can fail — proven on a value it must reject, so the
    # assertion above is not vacuous.
    with pytest.raises(AssertionError):
        _strict_loads(json.dumps({"code_hash": float("nan")}))


def test_a_written_document_reads_back_key_for_key(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    document = _document()
    (run_dir / IDENTITY_FILE).write_text(json.dumps(document, indent=2))
    read = read_identity(run_dir)
    assert read == document
    assert list(read) == list(document)
    assert _strict_loads((run_dir / IDENTITY_FILE).read_text()) == document


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("not json at all", id="unparseable"),
        pytest.param("[1, 2, 3]", id="a JSON array, not an object"),
        pytest.param('"a string"', id="a JSON string, not an object"),
    ],
)
def test_a_document_that_is_not_an_object_is_refused(tmp_path: Path, text: str):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    (run_dir / IDENTITY_FILE).write_text(text)
    with pytest.raises(ContractError) as e:
        read_identity(run_dir)
    assert e.value.code == "E-RESUME-NO-IDENTITY"


def test_an_absent_document_is_refused(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with pytest.raises(ContractError) as e:
        read_identity(run_dir)
    assert e.value.code == "E-RESUME-NO-IDENTITY"
    assert IDENTITY_FILE in str(e.value)


@pytest.mark.parametrize(
    "missing", ["code_hash", "parameters_hash", "uv_lock_hash", "config_path", "draft"]
)
def test_a_document_missing_any_one_key_is_refused(tmp_path: Path, missing: str):
    """Every key, one at a time. `draft` is the one a partial reader is
    likeliest to accept — it is the last key, and `false` reads as an absence
    to any check that tests truthiness rather than presence — so the
    parametrization covers all five rather than a representative one.
    """
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    document = _document()
    del document[missing]
    (run_dir / IDENTITY_FILE).write_text(json.dumps(document))
    with pytest.raises(ContractError) as e:
        read_identity(run_dir)
    assert e.value.code == "E-RESUME-NO-IDENTITY"
    assert missing in str(e.value)


def _run_dir_with_root(tmp_path: Path, recorded_root: str | None) -> Path:
    run_dir = allocate_run_dir(tmp_path / "results", HASH, WHEN)
    (run_dir / "environment").mkdir()
    if recorded_root is not None:
        (run_dir / "environment" / "repo_root.txt").write_text(recorded_root)
    return run_dir


def test_the_recorded_repo_root_is_read_back(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    run_dir = _run_dir_with_root(tmp_path, f"{repo}\n")
    assert read_repo_root(run_dir) == repo


@pytest.mark.parametrize(
    "recorded",
    [
        pytest.param(None, id="absent"),
        pytest.param("", id="empty"),
        pytest.param("   \n", id="whitespace only"),
        pytest.param("/no/such/directory/anywhere\n", id="not a directory"),
    ],
)
def test_an_unusable_repo_root_is_refused(tmp_path: Path, recorded: str | None):
    run_dir = _run_dir_with_root(tmp_path, recorded)
    with pytest.raises(ContractError) as e:
        read_repo_root(run_dir)
    assert e.value.code == "E-RESUME-NO-CONFIG"


def test_a_repo_root_naming_a_file_is_refused(tmp_path: Path):
    """The `is_dir` half specifically: a path that EXISTS and is not a
    directory, which an `exists()` check would accept."""
    target = tmp_path / "a_file"
    target.write_text("not a repo\n")
    run_dir = _run_dir_with_root(tmp_path, f"{target}\n")
    with pytest.raises(ContractError) as e:
        read_repo_root(run_dir)
    assert e.value.code == "E-RESUME-NO-CONFIG"


def _repo_with_config(tmp_path: Path, relative: str) -> Path:
    repo = tmp_path / "proj"
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("metadata: {}\n")
    return repo


@pytest.mark.parametrize(
    "relative",
    [
        pytest.param("config.yaml", id="at the root"),
        pytest.param("configs/cohort/config.yaml", id="nested, forward separators"),
        pytest.param("configs/cohort-pilot/config.yaml", id="a hyphenated component"),
    ],
)
def test_a_contained_config_path_resolves(tmp_path: Path, relative: str):
    """The HONOURING direction, which a refusal test never proves: a
    recorded relative path — separators included, since a recorded path is a
    path and not a filename — resolves to the file it names."""
    repo = _repo_with_config(tmp_path, relative)
    run_dir = _run_dir_with_root(tmp_path, f"{repo}\n")
    resolved = config_path_for(run_dir, repo, _document(config_path=relative))
    assert resolved == (repo / relative).resolve()
    assert resolved.read_text() == "metadata: {}\n"


def test_a_recorded_path_escaping_the_repo_root_is_refused(tmp_path: Path):
    """The POSITIVE CONTROL for the containment rule: a mutation that drops
    the check must fail here. The secret is real and outside the repo, and
    the assertion is that the call REFUSES — not merely that it returns
    something else — because a resolver that returned the escaped path would
    hand a caller a file to validate and execute against.
    """
    repo = _repo_with_config(tmp_path, "configs/config.yaml")
    secret = tmp_path.parent / "secret"
    secret.mkdir(exist_ok=True)
    (secret / "config.yaml").write_text("metadata: {}\n")
    run_dir = _run_dir_with_root(tmp_path, f"{repo}\n")
    escaping = _document(config_path="../../secret/config.yaml")
    # The escape really does resolve to an existing file, so the refusal
    # cannot be the file-existence check standing in for containment.
    assert (repo / "../../secret/config.yaml").resolve().is_file()
    with pytest.raises(ContractError) as e:
        config_path_for(run_dir, repo, escaping)
    assert e.value.code == "E-RESUME-NO-CONFIG"
    assert "containment" in str(e.value)


def test_an_absolute_recorded_path_is_refused_even_inside_the_repo(tmp_path: Path):
    """An absolute path is refused for its own reason, not by containment: a
    run directory's config location is derived from the repo it belongs to,
    so this fixture's absolute path points INSIDE the repo, where containment
    alone would accept it."""
    repo = _repo_with_config(tmp_path, "configs/config.yaml")
    run_dir = _run_dir_with_root(tmp_path, f"{repo}\n")
    inside = str((repo / "configs" / "config.yaml").resolve())
    assert Path(inside).is_file()
    with pytest.raises(ContractError) as e:
        config_path_for(run_dir, repo, _document(config_path=inside))
    assert e.value.code == "E-RESUME-NO-CONFIG"


@pytest.mark.parametrize(
    "recorded",
    [pytest.param("", id="empty"), pytest.param(None, id="null"), pytest.param(3, id="an int")],
)
def test_a_config_path_that_is_not_a_relative_string_is_refused(tmp_path: Path, recorded: object):
    repo = _repo_with_config(tmp_path, "configs/config.yaml")
    run_dir = _run_dir_with_root(tmp_path, f"{repo}\n")
    with pytest.raises(ContractError) as e:
        config_path_for(run_dir, repo, _document(config_path=recorded))
    assert e.value.code == "E-RESUME-NO-CONFIG"


def test_a_contained_path_naming_nothing_is_refused(tmp_path: Path):
    repo = _repo_with_config(tmp_path, "configs/config.yaml")
    run_dir = _run_dir_with_root(tmp_path, f"{repo}\n")
    with pytest.raises(ContractError) as e:
        config_path_for(run_dir, repo, _document(config_path="configs/gone.yaml"))
    assert e.value.code == "E-RESUME-NO-CONFIG"


def test_a_directory_named_by_a_contained_path_is_refused(tmp_path: Path):
    """The `is_file` half: a contained path that exists and is a directory,
    which an `exists()` check would accept."""
    repo = _repo_with_config(tmp_path, "configs/config.yaml")
    run_dir = _run_dir_with_root(tmp_path, f"{repo}\n")
    with pytest.raises(ContractError) as e:
        config_path_for(run_dir, repo, _document(config_path="configs"))
    assert e.value.code == "E-RESUME-NO-CONFIG"
