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


class SweptAway:
    """Marks a parameter that `sweep` varies, at a scope with no single value for it.

    `Node.__getattr__` raises when it resolves one, so the refusal fires on the read
    itself. A bare sentinel returned to the caller would not — the raise would land
    on some later attribute access, under the wrong identifier.
    """

    __slots__ = ("path",)

    def __init__(self, path: str) -> None:
        self.path = path


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
        value = data[name]
        if isinstance(value, SweptAway):
            raise ContractError(
                f"`{value.path}` is varied by `sweep`, so it has no single value at this "
                "scope; read it from a `condition`- or `repeat`-scoped step",
                code="E-STEP-SWEPT-PARAM",
            )
        return _wrap(value, full)

    def __setattr__(self, name: str, value: Any) -> None:
        raise ContractError(
            f"the config is immutable: cannot set {name!r}. A node is rebuilt on every "
            "access, so the write would land on a throwaway object — a step that held "
            f"one and read {name!r} back would see its own value while every fresh "
            "`cfg` access still returned what the config declares. The config is the "
            "record of what ran; change it in the file",
            code="E-CONFIG-IMMUTABLE",
        )

    def __delattr__(self, name: str) -> None:
        raise ContractError(
            f"the config is immutable: cannot delete {name!r}. A node is rebuilt on "
            "every access, so the deletion would land on a throwaway object and every "
            "fresh `cfg` access would still resolve the path. The config is the record "
            "of what ran; change it in the file",
            code="E-CONFIG-IMMUTABLE",
        )


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
