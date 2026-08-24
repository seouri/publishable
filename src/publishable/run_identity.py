"""Run identity and the directory lock. docs/reference.md § Run identity."""

import json
import os
import socket
import string
from datetime import UTC, datetime
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
                "A lock left by a killed process is reported, never assumed dead — "
                "for `run` and `draft`, and for every case a liveness test cannot answer.",
                code="E-RUN-LOCKED",
            ) from None
        with os.fdopen(fd, "w") as fh:
            # Three keys, and `started_at` is the third — which
            # `docs/reference.md` § One execution at a time already documented
            # while this payload held two (H9b plan § Corrections, correction
            # 9). It exists for the DIAGNOSTIC: a refusal that can say *held
            # since 2026-08-23T18:35:18Z by pid 41271 on this host* is the
            # difference between a legible refusal and a puzzle.
            #
            # **`resume`'s liveness test deliberately does not consult it**
            # (`_holder_is_dead` below, and the same sentence in that
            # document). An age threshold would answer *is this holder
            # alive?* with a stopwatch — a proxy — and a recycled pid under a
            # long-running holder would then read as dead and lose a live
            # run's directory. Reading only `pid` and `host` makes PID reuse
            # read as ALIVE and refuse, which is the conservative direction:
            # a refusal costs an operator one command, and a wrong takeover
            # costs two writers on one append-only tree.
            json.dump(
                {
                    "host": socket.gethostname(),
                    "pid": os.getpid(),
                    "started_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
                fh,
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.path.unlink(missing_ok=True)


TAKEOVER_FILE = "lock.takeover"


def _holder_is_dead(raw: str) -> bool:
    """Is the process named by `lock`'s contents provably gone?

    **`True` for exactly one reason** — `os.kill(pid, 0)` raising
    `ProcessLookupError` for a `pid` recorded against this machine's
    `socket.gethostname()` — and `False` for every other state, including
    every state this function cannot answer: unparseable JSON, a non-object,
    a missing or mistyped `host` or `pid`, a `host` that is not this
    machine's, a non-positive `pid` (`os.kill(0, 0)` addresses the whole
    process group, so it answers a different question), `kill` succeeding,
    `PermissionError` (the pid exists and belongs to another user), and any
    other `OSError`.

    Six of the seven states hold the lock, and the asymmetry is the point:
    a refusal costs an operator one command, while a wrong takeover puts two
    writers on one append-only tree, which is the failure the lock exists to
    prevent.

    **`started_at` is deliberately not read** — see `RunLock.__enter__`,
    where it is written, and `docs/reference.md` § One execution at a time,
    which says the same thing. A recycled pid therefore reads as *alive*
    and refuses.
    """
    try:
        holder = json.loads(raw)
    except ValueError:
        return False
    if not isinstance(holder, dict):
        return False
    host = holder.get("host")
    pid = holder.get("pid")
    if not isinstance(host, str) or host != socket.gethostname():
        return False
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return False


def take_over_dead_lock(run_dir: Path) -> None:
    """Steps 1-3 of `resume`'s lock takeover: claim an exclusive token,
    decide inside it, and unlink a `lock` whose holder is provably dead.
    `docs/reference.md` § Resuming and § One execution at a time.

    **Step 4 is the caller's ordinary `RunLock`**, and it is not here: the
    acquisition inside `cli._execute_prepared`'s `with RunLock(run_dir)` is
    what this ends with, whose `O_CREAT | O_EXCL` stays the only claim in
    the system. This function removes a claim; it never makes one.

    **The order is the whole of its correctness, and it was arrived at by
    falsifying two others.** Liveness-then-`os.rename` produced four winners
    of four processes on trial 0, and scan-then-claim two — both because a
    decision taken from the directory's state is stale by the time the claim
    is made. Contend first, decide second.

    **The residual, stated rather than hidden.** A takeover killed with
    `SIGKILL` between the token's creation and its release in the `finally`
    leaves `lock.takeover` behind, and every later `resume` then refuses
    `E-RUN-LOCKED` until the file is removed by hand — which the refusal's
    own message says. That window holds two syscalls and no user code, which
    is the reason nothing else is put inside it, and the `finally` covers
    every ordinary path including `BaseException`. This is a stated
    non-promise rather than an argument that it cannot happen.
    """
    token = run_dir / TAKEOVER_FILE
    lock = run_dir / "lock"
    try:
        fd = os.open(token, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ContractError(
            f"{token} exists, so another `resume` of {run_dir} is deciding this "
            "directory's lock right now. If no other `resume` is running, the file "
            "is a residual of one that was killed inside its own two-syscall "
            "window: remove it and try again.",
            code="E-RUN-LOCKED",
        ) from None
    try:
        try:
            raw = lock.read_text()
        except OSError:
            # Absent (or unreadable as a file at all) — nothing to reclaim,
            # and the caller's `RunLock` is the claim either way. Not an
            # error: the commonest crash leaves a lock behind, and a run
            # killed after `run.yaml` was written leaves none.
            return
        if not _holder_is_dead(raw):
            raise ContractError(
                f"{lock} is held: {raw.strip()}. `resume` takes over a lock only "
                "when its holder is provably gone — a pid recorded against this "
                "host that no longer exists — and reports every other state, "
                "including a lock recorded on another node, whose process table "
                "core cannot see.",
                code="E-RUN-LOCKED",
            )
        lock.unlink(missing_ok=True)
    finally:
        os.close(fd)
        token.unlink(missing_ok=True)


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

    **This is the THIRD reader of this file with these three refusals**, and
    the other two are named rather than left for a grep: `freeze` refuses
    `E-FREEZE-NO-CONFIG` for the same absent/empty/not-a-directory triple,
    and `report._read_repo_root` refuses `E-REPORT-OVERRIDE-REPO` for it.
    Not shared, and the reason is not convenience: `freeze`'s copy does not
    raise at all — it returns an exit code through its own `_refuse`, so it
    is not callable as a predicate — and consolidating the three would move a
    reader into this module and change what two SHIPPED commands raise and
    print. That is a behaviour change to `freeze` and `report`, outside this
    slice, and `freeze.py` is a file this task may not touch. Filed for
    consolidation rather than done quietly here.
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
