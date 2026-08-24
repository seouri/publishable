import json
import os
import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest

from publishable import ContractError, run_identity
from publishable.run_identity import (
    IDENTITY_FILE,
    TAKEOVER_FILE,
    RunLock,
    allocate_run_dir,
    config_path_for,
    identity_document,
    point_latest,
    read_identity,
    read_repo_root,
    take_over_dead_lock,
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


def _repo_with_config(base: Path, relative: str) -> Path:
    repo = base / "proj"
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
    # The repo is nested one level deeper than the other fixtures' so the
    # escape target stays inside `tmp_path`: a test writing into the shared
    # pytest root is a test that can collide with another test's fixture.
    repo = _repo_with_config(tmp_path / "work", "configs/config.yaml")
    secret = tmp_path / "secret"
    secret.mkdir()
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


# --- H9b task 14: the lock's third key and `resume`'s takeover -------------
# Ruling W / design Decision 2. The mutual exclusion's END-TO-END pin is
# guard-pin arm G in `tests/test_cli.py` (two `main(["resume", ...])` threads);
# the tests below pin the protocol's own states, which arm G cannot separate
# because it drives one directory through one verdict.


def _dead_pid() -> int:
    """A pid that is provably gone: a subprocess this process reaped.

    Never a fabricated number — a fabricated pid makes every one of these
    fixtures agree with a liveness test that always answers *dead*, and this
    file has no other way to tell the two apart.
    """
    import subprocess
    import sys

    child = subprocess.Popen([sys.executable, "-c", ""])
    assert child.wait(timeout=60) == 0
    with pytest.raises(ProcessLookupError):
        os.kill(child.pid, 0)
    return child.pid


def _crashed(tmp_path: Path, holder: object | str) -> Path:
    """A run directory whose `lock` holds `holder` — a mapping is dumped, a
    string is written raw so a non-JSON arm is reachable."""
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    text = holder if isinstance(holder, str) else json.dumps(holder)
    (run_dir / "lock").write_text(text)
    return run_dir


def test_the_lock_records_three_keys_and_the_third_is_the_start_time(tmp_path: Path):
    """§ One execution at a time says `lock` records the host, pid and start
    time; the payload held two keys until this task (plan § Corrections,
    correction 9). An equality over the key set, not a containment: a fourth
    key would be a documented field nobody wrote a sentence for."""
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):
        holder = json.loads((run_dir / "lock").read_text())
    assert set(holder) == {"host", "pid", "started_at"}
    assert holder["pid"] == os.getpid()
    assert holder["host"] == socket.gethostname()
    # The format the rest of this project stamps a UTC instant in
    # (`runner`'s `started_at`, `apparatus`'s `at`), parsed rather than
    # regex-matched so a wrong offset or a local-time value fails here.
    assert datetime.strptime(holder["started_at"], "%Y-%m-%dT%H:%M:%SZ").tzinfo is None


def test_a_lock_with_no_started_at_and_a_dead_pid_is_taken_over(tmp_path: Path):
    """**The structural assertion the `started_at` mutation is owed.** No
    fixture can force a recycled pid, so the mutation *consult `started_at`
    in the liveness test* is blind by construction; this is its replacement.
    A liveness test that read `started_at` — an age threshold, a
    freshness window, anything — would have to refuse a lock that has no
    such key, and this asserts the takeover proceeds. A lock written by a
    build that predates the third key is exactly this shape."""
    run_dir = _crashed(tmp_path, {"host": socket.gethostname(), "pid": _dead_pid()})
    take_over_dead_lock(run_dir)
    assert (run_dir / "lock").exists() is False
    assert (run_dir / TAKEOVER_FILE).exists() is False


def test_a_dead_holders_lock_is_unlinked_and_the_token_released(tmp_path: Path):
    run_dir = _crashed(
        tmp_path,
        {"host": socket.gethostname(), "pid": _dead_pid(), "started_at": "2026-08-23T18:35:18Z"},
    )
    take_over_dead_lock(run_dir)
    assert (run_dir / "lock").exists() is False
    assert (run_dir / TAKEOVER_FILE).exists() is False
    # And the ordinary claim then succeeds — the takeover removes a claim and
    # never makes one, so step 4 is still what holds the directory.
    with RunLock(run_dir):
        assert (run_dir / "lock").is_file()


def test_an_absent_lock_is_nothing_to_reclaim(tmp_path: Path):
    """Step 2's `absent → step 4` arm. Asserted positively — the token is
    gone AND the directory is claimable — because a control asserting only
    that nothing raised passes identically if the function returned early
    for the wrong reason."""
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    take_over_dead_lock(run_dir)
    assert (run_dir / TAKEOVER_FILE).exists() is False
    with RunLock(run_dir):
        assert (run_dir / "lock").is_file()


def test_a_live_holder_is_refused_and_its_lock_survives(tmp_path: Path):
    """Fixture F: the holder is THIS process, so `os.kill(pid, 0)` genuinely
    succeeds. The surviving `lock` is asserted, not just the code: a
    takeover that refused *and* unlinked would pass a code-only test and
    lose a live run's directory."""
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):
        with pytest.raises(ContractError) as e:
            take_over_dead_lock(run_dir)
        assert e.value.code == "E-RUN-LOCKED"
        assert (run_dir / "lock").is_file()
        assert (run_dir / TAKEOVER_FILE).exists() is False


@pytest.mark.parametrize(
    "holder",
    [
        pytest.param("not json at all {", id="unparseable"),
        pytest.param("[1, 2]", id="a JSON array"),
        pytest.param('"a string"', id="a JSON string"),
        pytest.param({"pid": 1}, id="no host"),
        pytest.param({"host": 3, "pid": 1}, id="a host of the wrong type"),
        pytest.param({"host": "some-other-node.example"}, id="no pid"),
        pytest.param({"host": "some-other-node.example", "pid": 1}, id="a foreign host"),
        pytest.param({"host": "H", "pid": "41271"}, id="a pid of the wrong type"),
        pytest.param({"host": "H", "pid": True}, id="a pid that is a bool"),
        pytest.param({"host": "H", "pid": 0}, id="a pid of zero"),
        pytest.param({"host": "H", "pid": -1}, id="a negative pid"),
    ],
)
def test_every_undecidable_lock_is_held(tmp_path: Path, holder: object):
    """Fixture G: each state the liveness test cannot answer refuses, and
    the lock SURVIVES each refusal. `H` is replaced by this machine's own
    hostname where the arm is about the pid rather than the host, so those
    arms fail for the reason they name."""
    if isinstance(holder, dict) and holder.get("host") == "H":
        holder = {**holder, "host": socket.gethostname()}
    run_dir = _crashed(tmp_path, holder)
    before = (run_dir / "lock").read_text()
    with pytest.raises(ContractError) as e:
        take_over_dead_lock(run_dir)
    assert e.value.code == "E-RUN-LOCKED"
    assert (run_dir / "lock").read_text() == before
    assert (run_dir / TAKEOVER_FILE).exists() is False


def test_a_kill_that_raises_permissionerror_holds_the_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The pid exists and belongs to another user. Reached through a
    monkeypatch because a foreign-uid process cannot be created here, and
    the patch is aimed at `run_identity`'s own `os.kill` — the name the
    liveness test calls — so a test that stopped calling it fails loudly
    rather than passing inert."""
    run_dir = _crashed(tmp_path, {"host": socket.gethostname(), "pid": _dead_pid()})

    def kill(pid: int, sig: int) -> None:
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(run_identity.os, "kill", kill)
    with pytest.raises(ContractError) as e:
        take_over_dead_lock(run_dir)
    assert e.value.code == "E-RUN-LOCKED"
    assert (run_dir / "lock").is_file()


def test_a_kill_that_raises_another_oserror_holds_the_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The `except OSError` arm below `ProcessLookupError`, which is a
    subclass of it: an arm ordered the other way round would answer *dead*
    for every failure and this test would still pass, so the dead arm is
    pinned by `..._is_taken_over` above and this one pins the general
    failure."""
    run_dir = _crashed(tmp_path, {"host": socket.gethostname(), "pid": _dead_pid()})

    def kill(pid: int, sig: int) -> None:
        raise OSError(999, "something else entirely")

    monkeypatch.setattr(run_identity.os, "kill", kill)
    with pytest.raises(ContractError) as e:
        take_over_dead_lock(run_dir)
    assert e.value.code == "E-RUN-LOCKED"
    assert (run_dir / "lock").is_file()


def test_an_existing_token_refuses_and_leaves_both_files_alone(tmp_path: Path):
    """Step 1: `FileExistsError` on the token is `E-RUN-LOCKED`, and the
    residual is named in the message with its remedy. The `lock` must
    survive — a refusal at the token has decided nothing about the holder —
    and the token must NOT be removed, since this call did not create it."""
    run_dir = _crashed(tmp_path, {"host": socket.gethostname(), "pid": _dead_pid()})
    (run_dir / TAKEOVER_FILE).write_text("")
    with pytest.raises(ContractError) as e:
        take_over_dead_lock(run_dir)
    assert e.value.code == "E-RUN-LOCKED"
    assert TAKEOVER_FILE in str(e.value)
    assert "remove it" in str(e.value)
    assert (run_dir / "lock").is_file()
    assert (run_dir / TAKEOVER_FILE).is_file()


def test_the_token_is_released_when_the_liveness_test_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The `finally` covers `BaseException`, not only the coded refusals: a
    `KeyboardInterrupt` out of the middle of the decision must still leave
    no residual, or one Ctrl-C would make every later `resume` refuse."""
    run_dir = _crashed(tmp_path, {"host": socket.gethostname(), "pid": _dead_pid()})

    def kill(pid: int, sig: int) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(run_identity.os, "kill", kill)
    with pytest.raises(KeyboardInterrupt):
        take_over_dead_lock(run_dir)
    assert (run_dir / TAKEOVER_FILE).exists() is False
    assert (run_dir / "lock").is_file()


def test_two_threads_racing_one_dead_holder_reach_one_holder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The protocol's mutual exclusion at the level of the two shipped
    functions — `take_over_dead_lock` then `RunLock`, in that order, which is
    what `command_resume` calls.

    **Not a guard-pin arm** (task 1 was the only task that may create one):
    arm G pins the same property end to end through `main(["resume", ...])`,
    and this exists because arm G cannot run until `resume` dispatches. The
    five-process probe against the shipped code is the discovery instrument,
    reported in the batch report — a probe proves the moment, a test proves
    tomorrow.

    **The interleaving is asymmetric, and a symmetric one does not catch the
    violation** — measured, not reasoned: a first version released both
    threads together inside the liveness syscall, and deleting the token's
    `O_EXCL` left it GREEN, because two threads that unlink before either
    creates still meet `RunLock`'s own exclusive create and exactly one wins.
    The violation the token exists to prevent needs a **stale verdict**: one
    thread judging the OLD holder dead, the other then taking the lock, and
    the first thread waking up to unlink a LIVE holder's lock and create its
    own. So the first arrival at the liveness syscall is held there — between
    its verdict's evidence and the lock's replacement — until the other
    thread holds the lock.

    Under the shipped protocol the second thread never reaches that syscall
    at all: it refuses at the exclusive token, the event is never set, the
    first arrival's wait times out, and the takeover proceeds. Under the
    mutation both arrive, the ordering above is forced, and two holders
    appear. The hook's own call count is asserted, so a patch aimed at a name
    the code stopped calling fails rather than passing inert.
    """
    import threading

    dead = _dead_pid()
    run_dir = _crashed(tmp_path, {"host": socket.gethostname(), "pid": dead})
    real_kill = run_identity.os.kill
    hits: list[int] = []
    held: list[str] = []
    refused: list[str] = []
    guard = threading.Lock()
    winner_holds = threading.Event()

    def kill(pid: int, sig: int) -> None:
        if pid != dead:
            return real_kill(pid, sig)
        with guard:
            hits.append(pid)
            arrival = len(hits)
        if arrival == 1:
            # Held inside the liveness syscall until the other thread holds
            # the lock — or for two seconds, which is what happens under the
            # shipped protocol, where no other thread ever gets here.
            winner_holds.wait(timeout=2.0)
        return real_kill(pid, sig)

    monkeypatch.setattr(run_identity.os, "kill", kill)

    def contend(name: str) -> None:
        try:
            take_over_dead_lock(run_dir)
            with RunLock(run_dir):
                with guard:
                    held.append(name)
                winner_holds.set()
                # Held while the other thread is awake, so a second holder
                # overlaps this one rather than following it.
                threading.Event().wait(0.3)
        except ContractError as exc:
            assert exc.code == "E-RUN-LOCKED", exc.code
            with guard:
                refused.append(name)

    threads = [threading.Thread(target=contend, args=(f"t{i}",)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not any(thread.is_alive() for thread in threads)
    assert hits, "the liveness hook never fired — the patch was aimed at a dead name"
    assert len(held) == 1, (held, refused)
    assert len(refused) == 1, (held, refused)
    assert (run_dir / TAKEOVER_FILE).exists() is False
