"""`.env` loading and the credential values core read.

docs/reference.md § Secrets & credentials. A config holds an environment
variable's NAME; the value lives in `.env`, which every scaffold gitignores.

**Never touches provenance**, and the claim is structural rather than careful:
nothing in this module imports `publishable.provenance` or writes into the
document it builds, and `provenance.environment` is assembled from `os`,
`hostname`, `hardware` and `uv.lock` alone. The one surface on which a value
could reach a record is a failing step's exception text, which `redact` below
exists for.
"""

import os
from collections.abc import Iterable, Mapping
from pathlib import Path

from dotenv.main import DotEnv

ENV_FILENAME = ".env"


def load_env(repo_root: Path | None) -> bool:
    """Load `<repo_root>/.env` into `os.environ`.

    Returns whether parsing found at least one entry — **not** "a file was
    read": a comment-only or empty `.env` returns `False`, and a load whose
    every binding is skipped because the shell already set it returns `True`.
    No caller depends on the distinction — it is returned rather than dropped
    so a caller that later needs it has it, and described here so nobody reads
    it as a file-existence test.

    **Never overrides.** A variable already exported in the shell wins over
    the file, which is the direction that fails safe: a stale `.env` cannot
    silently redirect a run to the wrong account, and a machine that supplies
    its credentials through a secret manager needs no file at all. This
    includes `${VAR}` interpolation inside the file: `dotenv.main.DotEnv` is
    called with `override=False` directly, and that flag is what decides
    whether a `${VAR}` reference resolves against the shell or against the
    file being parsed — not only what gets written afterward. Built from
    `DotEnv(...).dict()` plus `os.environ.setdefault` rather than
    `load_dotenv` itself, deliberately: `load_dotenv` honours
    `PYTHON_DOTENV_DISABLED`, an undocumented environment variable that
    changes behavior with no flag and no config field — exactly what
    `CLAUDE.md`'s first invariant rules out for anything this repo builds.
    `DotEnv.dict()`, like the `dotenv_values` helper it underlies, does not
    consult it (it only parses and returns a mapping; it never touches
    `os.environ` itself), so building the override-safe write here instead
    closes that gap rather than inheriting it. A key written bare (`FOO`, no
    `=value`) parses to `None` rather than `""`; skipped rather than set,
    which lands in the same place `missing_env` would either way, since it
    already treats an empty value as missing.

    Idempotent, because it is called twice on a `run` — once by `validate` and
    once before any step executes — and a second load can only re-set what is
    already set, `setdefault` being exactly `override=False`.

    A `None` root (no git repository) and a directory holding no `.env` are both
    quiet: a project whose credentials are exported rather than filed is ordinary,
    and this function has no way to tell it from one that forgot. Whether a
    *declared* variable is missing is `missing_env`'s question, asked by
    `validate` against what a template declares.
    """
    if repo_root is None:
        return False
    path = repo_root / ENV_FILENAME
    if not path.is_file():
        return False
    values = DotEnv(path, stream=None, verbose=False, interpolate=True, override=False).dict()
    for key, value in values.items():
        if value is None:
            continue
        os.environ.setdefault(key, value)
    return bool(values)


def missing_env(names: Iterable[str]) -> list[str]:
    """Declared names with no value, in declared order, each named once.

    An empty string counts as missing: a name exported with no value is one
    somebody wrote down and did not fill in, which is the fault this family
    exists to catch.
    """
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        if not os.environ.get(name):
            out.append(name)
    return out


def credential_values(names: Iterable[str]) -> dict[str, str]:
    """The values core read for the declared names — `{name: value}`, unset omitted.

    This is the knowledge `redact` answers from, and the whole of decision 4: core
    can say *is this the value I read out of the environment* rather than *does
    this look like a secret*. A pattern check fails open on a credential named
    `instrument_pw` and fails closed on a config value that happens to look
    random.

    Held only for the length of one command, and never written anywhere: the
    mapping is built where a run starts and reaches exactly one consumer.
    """
    found: dict[str, str] = {}
    for name in names:
        value = os.environ.get(name)
        if value:
            found[name] = value
    return found


def redact(text: str | None, values: Mapping[str, str]) -> str | None:
    """Replace each credential value in `text` with a marker naming its variable.

    Longest value first, so a credential whose value is a prefix of another's
    cannot leave the longer one half-exposed as `<redacted:SHORT>def` — which
    would read as a redaction while being a leak.

    Says a redaction happened rather than scrubbing silently: the record exists to
    be debugged from, and `<redacted:OPENAI_API_KEY>` tells a reader both what was
    removed and which variable to look at, without telling them the value.
    """
    if not text or not values:
        return text
    for name, value in sorted(values.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if value:
            text = text.replace(value, f"<redacted:{name}>")
    return text
