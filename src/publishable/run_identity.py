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
    raise ContractError(
        f"26 runs already share the id {base}", code="E-RUN-ID-EXHAUSTED"
    )


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
            json.dump(
                {"host": socket.gethostname(), "pid": os.getpid()}, fh
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.path.unlink(missing_ok=True)
