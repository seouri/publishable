"""Run identity and the directory lock. docs/reference.md § Run identity."""

import json
import os
import socket
import string
from datetime import datetime
from pathlib import Path
from types import TracebackType

from publishable.errors import ContractError
from publishable.hashes import short


def allocate_run_dir(output_dir: Path, code_hash: str, when: datetime) -> Path:
    """First free name. A collision takes a suffix, never more clock precision."""
    stamp = when.strftime("%Y-%m-%dT%H-%M-%SZ")
    base = f"run_{stamp}_{short(code_hash)}"
    output_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ("", *(f"_{c}" for c in string.ascii_lowercase[1:])):
        candidate = output_dir / (base + suffix)
        try:
            # mkdir IS the claim. Checking `exists()` first would leave a window
            # in which two runs started in the same second both see it free —
            # exactly the shell-loop and scheduler cases this suffix exists for.
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise ContractError(f"26 runs already share the id {base}", code="E-RUN-ID-EXHAUSTED")


def point_latest(output_dir: Path, run_dir: Path) -> None:
    """A pointer, not an artifact. Falls back to latest.txt without symlinks.

    Exactly one pointer form exists after a call: whichever one succeeds
    clears the other, so a caller reading either never resolves to a run
    left behind by an earlier call that took the other path.
    """
    link = output_dir / "latest"
    text = output_dir / "latest.txt"
    try:
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(run_dir.name)
        text.unlink(missing_ok=True)
    except (OSError, NotImplementedError):
        text.write_text(run_dir.name + "\n")
        if link.is_symlink() or link.exists():
            link.unlink()


class RunLock:
    """A run holds its directory while it executes."""

    def __init__(self, run_dir: Path) -> None:
        self.path = run_dir / "lock"

    def __enter__(self) -> "RunLock":
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                holder = self.path.read_text().strip()
            except OSError:
                holder = "unknown (lock file unreadable or removed)"
            raise ContractError(
                f"{self.path} is held: {holder}. "
                "A lock left by a killed process is reported, never assumed dead.",
                code="E-RUN-LOCKED",
            ) from None
        with os.fdopen(fd, "w") as fh:
            json.dump({"host": socket.gethostname(), "pid": os.getpid()}, fh)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.path.unlink(missing_ok=True)


IDENTITY_FILE = "identity.json"


def identity_document(
    *,
    code_hash: str,
    parameters_hash: str,
    uv_lock_hash: str | None,
    config_path_rel: str,
    draft: bool,
) -> dict[str, object]:
    """What a run makes durable before it executes, so a second entry can
    compare against it. `docs/reference.md` § Resuming.

    Five keys, in this order: exactly what a second entry cannot compute and
    cannot wait for `run.yaml` to hold, and nothing it will not read.
    `code_hash` is not recoverable from a crashed directory at all;
    `parameters_hash` and `uv_lock_hash` are recomputable, which is the
    point — the recorded figure is what makes an EDIT detectable;
    `config_path` is the file the run was started from, without which a
    resume cannot re-enter the same phases; and `draft`, because a resumed
    draft that recorded `draft: false` would be citable.

    `input_manifest_hash` is deliberately absent: `manifest/input.json` is
    itself the durable operand, so its digest would be a figure with no
    reader.

    `config_path_rel` is POSIX-separated and relative to the repo root. This
    function neither resolves it nor checks it — the containment check
    belongs where the value is READ (`config_path_for`), because that is
    where a path from a file is about to be used.
    """
    return {
        "code_hash": code_hash,
        "parameters_hash": parameters_hash,
        "uv_lock_hash": uv_lock_hash,
        "config_path": config_path_rel,
        "draft": draft,
    }


_IDENTITY_KEYS = ("code_hash", "parameters_hash", "uv_lock_hash", "config_path", "draft")


def read_identity(run_dir: Path) -> dict[str, object]:
    """`<run_dir>/identity.json`, or `E-RESUME-NO-IDENTITY`.

    One code for four faults — absent, unparseable, not an object, missing a
    key — because the remedy is the same for all four: run again into a fresh
    `run_<id>/`. A directory that predates this artifact and one edited by
    hand are indistinguishable from here, and the message says so rather than
    guessing which happened.

    No fallback to the run ID's own 7-hex `code_hash` prefix: it says nothing
    about `parameters` or the lockfile, so a comparison covering one of three
    figures would read as three.
    """
    path = run_dir / IDENTITY_FILE
    try:
        raw = path.read_text()
    except OSError:
        raise ContractError(
            f"{path} is absent or unreadable, so this run's identity claims cannot be "
            "compared: either it was written by a build that predates the file, or the "
            "directory was edited. Run again into a fresh run directory.",
            code="E-RESUME-NO-IDENTITY",
        ) from None
    try:
        document = json.loads(raw)
    except ValueError:
        raise ContractError(
            f"{path} is not valid JSON",
            code="E-RESUME-NO-IDENTITY",
        ) from None
    if not isinstance(document, dict):
        raise ContractError(
            f"{path} holds {type(document).__name__}, not an object with the keys "
            f"{', '.join(_IDENTITY_KEYS)}",
            code="E-RESUME-NO-IDENTITY",
        )
    missing = [key for key in _IDENTITY_KEYS if key not in document]
    if missing:
        raise ContractError(
            f"{path} is missing {', '.join(missing)}",
            code="E-RESUME-NO-IDENTITY",
        )
    return document


def read_repo_root(run_dir: Path) -> Path:
    """The repo the run was started from, out of `environment/repo_root.txt`.

    `E-RESUME-NO-CONFIG` when the file is absent, holds nothing, or names
    something that is not a directory — the same code `config_path_for`
    raises, because both halves answer one question (*can the config this run
    executed be found?*) and share one remedy (restore the directory).

    Split from `config_path_for` rather than folded into it so the value is
    read ONCE: a caller re-entering a run needs this root for itself, and a
    second read of the same file inside the resolver would be a second answer
    to a question already answered.
    """
    path = run_dir / "environment" / "repo_root.txt"
    try:
        recorded = path.read_text().strip()
    except OSError:
        raise ContractError(
            f"{path} is absent or unreadable, so the repository this run was started "
            "from is unknown",
            code="E-RESUME-NO-CONFIG",
        ) from None
    if not recorded:
        raise ContractError(f"{path} is empty", code="E-RESUME-NO-CONFIG")
    root = Path(recorded)
    if not root.is_dir():
        raise ContractError(
            f"{path} names {recorded}, which is not a directory",
            code="E-RESUME-NO-CONFIG",
        )
    return root


def config_path_for(run_dir: Path, repo_root: Path, document: dict[str, object]) -> Path:
    """The config file a run was started from: `document["config_path"]`
    resolved under `repo_root`, refused if it does not stay there.

    **Containment, and nothing else.** A forward separator stays legal — a
    recorded path is a relative path with components, not a filename — so
    this checks where the value RESOLVES and never the shape of the string:
    `..` segments are refused by the containment check rather than by
    inspecting the text, and an absolute recorded path is refused outright,
    since the location of a run's config is derived from the repo it belongs
    to and is not a recorded string's to choose.

    This is `artifacts.StepIO._contained`'s rule, restated here rather than
    called: that predicate raises `ArtifactError` against a step's own
    directory layout, and this raises `ContractError` · `E-RESUME-NO-CONFIG`
    against a repo root. The reason the rule exists at all is H8a's: a name
    documented as relative would otherwise resolve `../../secret/x.json`, and
    a path read out of a FILE and then used is exactly that shape.

    **This is not a boundary and must not be written up as one.** A step can
    `open()` any file on the machine regardless, and core never inspects the
    body of user Python. What the rule buys is that a recorded config path
    resolves inside the repository it names, so an edited or hand-written
    record fails loudly instead of quietly validating some other file.
    """
    recorded = document["config_path"]
    if not isinstance(recorded, str) or not recorded:
        raise ContractError(
            f"{run_dir / IDENTITY_FILE} records config_path {recorded!r}, not a "
            "non-empty relative path",
            code="E-RESUME-NO-CONFIG",
        )
    candidate = (repo_root / recorded).resolve()
    resolved_root = repo_root.resolve()
    if Path(recorded).is_absolute() or not str(candidate).startswith(str(resolved_root) + os.sep):
        raise ContractError(
            f"{run_dir / IDENTITY_FILE} records config_path {recorded!r}, which "
            f"resolves outside {resolved_root} — checked for containment only (a `..` "
            "escape, an absolute path, or a symlink leading outside), never for its "
            "shape: a forward separator is legal",
            code="E-RESUME-NO-CONFIG",
        )
    if not candidate.is_file():
        raise ContractError(
            f"{candidate} does not exist or is not a file, so the config this run "
            "executed cannot be re-read",
            code="E-RESUME-NO-CONFIG",
        )
    return candidate
