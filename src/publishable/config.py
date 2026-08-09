"""The only module that parses YAML. See docs/reference.md § The importable surface."""

import difflib
from pathlib import Path
from typing import Any

import yaml

from publishable.errors import ContractError


def _wrap(value: Any, path: str) -> Any:
    if isinstance(value, dict):
        return Node(value, path)
    if isinstance(value, list):
        return [_wrap(v, f"{path}[{i}]") for i, v in enumerate(value)]
    return value


class Node:
    """Dot-access and nothing else, so no parameter name can be shadowed."""

    def __init__(self, data: dict[str, Any], path: str = "") -> None:
        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_path", path)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        data: dict[str, Any] = object.__getattribute__(self, "_data")
        base: str = object.__getattribute__(self, "_path")
        full = f"{base}.{name}" if base else name
        if name not in data:
            near = difflib.get_close_matches(name, list(data), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            raise ContractError(
                f"{full} is not a path this config holds{hint}", code="E-STEP-PARAM-UNKNOWN"
            )
        return _wrap(data[name], full)


class Config(Node):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data, "")

    @property
    def raw(self) -> dict[str, Any]:
        return dict(object.__getattribute__(self, "_data"))


def load_config(path: Path) -> Config:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ContractError(f"{path} does not parse as a mapping", code="E-CONFIG-PARSE")
    return Config(data)
