"""uv is not optional. S1 hashes the lockfile; syncing arrives with `reproduce`."""

import hashlib
import sys
from pathlib import Path


def environment_manager() -> str | None:
    """`"uv"` when this interpreter's environment was created by uv; `None` otherwise.

    `provenance.environment.manager` used to be the literal `"uv"`, written
    unconditionally — a record asserting an environment fact nothing measured,
    which is exactly what the rest of this key's siblings are not: `uv_lock_hash`
    is a digest of a file that was read, `os` a composition of three values the
    platform answered, `hardware.cpu_count` whatever `os.cpu_count()` said,
    `None` included.

    The measurement is `pyvenv.cfg`'s own `uv` key, and it is the direct
    question rather than a proxy. uv writes `uv = <version>` into the
    `pyvenv.cfg` of every environment it creates, so the file answers *what made
    this environment* — which is what the record claims. `shutil.which("uv")`
    was the alternative and is a correlate: it answers *is uv installed on this
    machine*, so it says `"uv"` for a hand-built venv that uv never touched and
    `None` for a uv-made one on a machine uv was later removed from. Both
    answers are wrong about the environment the numbers came through.

    **What happens when uv is absent: the key is `None`, and nothing warns.**
    `None` is this format's spelling for never-captured — `hardware.cpu_count`
    and `uv_lock`/`uv_lock_hash` already write it through rather than
    substituting a plausible value — and the actionable case, an environment no
    lockfile pins, already has its own diagnostic in `W-ENV-UNLOCKED`. A second
    warning here would be a registry seat for a fact that changes nothing a
    reader can act on: `manager` is a measurement, the way `git.code_dirty` is.

    Not gated on `sys.prefix != sys.base_prefix`. A non-virtual interpreter has
    no `pyvenv.cfg` at all, so the read already answers `None` for it, and a
    second predicate answering the same question is how two spellings of one
    fact drift apart.
    """
    cfg = Path(sys.prefix) / "pyvenv.cfg"
    try:
        text = cfg.read_text()
    except OSError:
        return None
    for line in text.splitlines():
        key, _, _ = line.partition("=")
        if key.strip() == "uv":
            return "uv"
    return None


def uv_lock_info(repo_root: Path) -> tuple[Path | None, str | None]:
    lock = repo_root / "uv.lock"
    if not lock.is_file():
        return None, None
    return lock, "sha256:" + hashlib.sha256(lock.read_bytes()).hexdigest()
