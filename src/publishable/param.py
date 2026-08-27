"""One parameter's type, default, constraints and help text.

The constraint vocabulary is closed on purpose: docs/reference.md § Templates.

`requires_env` is the one keyword here that is **not** a constraint and is
deliberately absent from that closed table: it constrains the *environment* a
value may be used in, not the value. `docs/reference.md` § A credential can belong to a parameter
value states the boundary and the reason — the provider is something you decide,
so it is a `Param`, and what that decision requires travels with it.
"""

import re
from collections.abc import Callable
from typing import Any

MISSING = object()
_TYPE_NAMES = {str: "string", int: "integer", float: "float", bool: "bool", list: "list"}


def _joined(values: list[Any]) -> str:
    return ", ".join(str(v) for v in values)


class Param:
    def __init__(
        self,
        type_: type,
        *,
        default: Any = MISSING,
        choices: list[Any] | None = None,
        ge: float | None = None,
        gt: float | None = None,
        le: float | None = None,
        lt: float | None = None,
        pattern: str | None = None,
        item_type: type | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        nullable: bool = False,
        requires_env: dict[Any, list[str]] | None = None,
        help: str | None = None,
    ) -> None:
        if type_ not in _TYPE_NAMES:
            raise ValueError(f"unsupported Param type {type_!r}")
        if default is None and not nullable:
            raise ValueError("default=None requires nullable=True")
        if pattern is not None and type_ is not str:
            raise ValueError(f"pattern requires type_=str, not {_TYPE_NAMES[type_]}")
        if (ge is not None or gt is not None or le is not None or lt is not None) and type_ not in (
            int,
            float,
        ):
            raise ValueError(
                f"ge/gt/le/lt require type_=int or type_=float, not {_TYPE_NAMES[type_]}"
            )
        if requires_env is not None:
            if choices is None:
                raise ValueError(
                    "requires_env requires choices: a credential requirement is "
                    "only checkable over a closed set of values"
                )
            absent = [c for c in choices if c not in requires_env]
            extra = [k for k in requires_env if k not in choices]
            if absent or extra:
                detail = ""
                if absent:
                    detail += f"; no key for {_joined(absent)}"
                if extra:
                    detail += f"; keys naming no choice: {_joined(extra)}"
                raise ValueError(
                    "requires_env must be total over choices: "
                    f"choices are {_joined(choices)}; "
                    f"requires_env names {_joined(list(requires_env))}{detail}"
                )
        self.type_ = type_
        self.default = default
        self.choices = choices
        self.ge, self.gt, self.le, self.lt = ge, gt, le, lt
        self.pattern = pattern
        self.item_type = item_type
        self.min_items, self.max_items = min_items, max_items
        self.nullable = nullable
        self.requires_env = requires_env
        self.help = help

    @property
    def required(self) -> bool:
        return self.default is MISSING

    def check(self, value: Any) -> str | None:
        """Return an error message, or None when the value is legal."""
        if value is None:
            return None if self.nullable else "is null, but the parameter is not nullable"
        if not self._is_type(value, self.type_):
            return f"is {value!r}, expected {_TYPE_NAMES[self.type_]}"
        if self.choices is not None and value not in self.choices:
            joined = ", ".join(str(c) for c in self.choices)
            return f"is {value!r}, expected one of {joined}"
        bounds: list[tuple[float | None, Callable[[Any, float], bool], str]] = [
            (self.ge, lambda v, b: v >= b, ">="),
            (self.gt, lambda v, b: v > b, ">"),
            (self.le, lambda v, b: v <= b, "<="),
            (self.lt, lambda v, b: v < b, "<"),
        ]
        for bound, op, sym in bounds:
            if bound is not None and not op(value, bound):
                return f"is {value!r}, expected {sym} {bound}"
        if (
            self.pattern is not None
            and isinstance(value, str)
            and not re.match(self.pattern, value)
        ):
            return f"is {value!r}, expected to match {self.pattern}"
        if self.type_ is list:
            return self._check_list(value)
        return None

    def _check_list(self, value: list[Any]) -> str | None:
        if self.item_type is not None:
            for i, item in enumerate(value):
                if not self._is_type(item, self.item_type):
                    return f"[{i}] is {item!r}, expected {_TYPE_NAMES[self.item_type]}"
        if self.min_items is not None and len(value) < self.min_items:
            return f"has {len(value)} items, expected at least {self.min_items}"
        if self.max_items is not None and len(value) > self.max_items:
            return f"has {len(value)} items, expected at most {self.max_items}"
        return None

    @staticmethod
    def _is_type(value: Any, expected: type) -> bool:
        if expected is bool:
            return isinstance(value, bool)
        if isinstance(value, bool):
            return False  # a bool is not an int here
        if expected is float:
            return isinstance(value, int | float)
        return isinstance(value, expected)

    def comment(self) -> str:
        """The inline comment `init` renders: requiredness, then one constraint or `help`.

        Requiredness leads for the reason `constraints()` gives below — it
        constrains what a config may write and it is what a reader needs first —
        and this method is the other rendering of the same vocabulary, the config
        line rather than the documentation table. It reported requiredness nowhere
        until 2026-08-27, which is how § Templates came to describe a `# REQUIRED`
        marker `init` did not write; `docs/superpowers/W5-SCOPING.md` § 2 has the
        measurement.

        The format is `metadata.description`'s, which is what the document
        compares it to: `REQUIRED — <text>` where there is text, `REQUIRED` alone
        where a required parameter carries neither a constraint nor `help`.
        """
        body = self._comment_body()
        if self.required:
            return f"REQUIRED — {body}" if body else "REQUIRED"
        return body

    def _comment_body(self) -> str:
        """One constraint claims the comment, else `help`.

        A `choices` comment additionally carries each value's `requires_env`
        variables. Those are not a constraint — see this module's docstring —
        and they are rendered against *every* choice rather than the written
        one, because nothing ever writes back into a config and a comment about
        the current value would be wrong the first time the file was edited.
        """
        if self.choices is not None:
            return "choices: " + " | ".join(self._choice_label(c) for c in self.choices)
        if self.gt is not None and self.lt is not None:
            return f"float in ({self.gt}, {self.lt})"
        for bound, sym in ((self.ge, ">="), (self.gt, ">"), (self.le, "<="), (self.lt, "<")):
            if bound is not None:
                return f"{_TYPE_NAMES[self.type_]} {sym} {bound}"
        if self.pattern is not None:
            return f"matches {self.pattern}"
        if self.type_ is list and self.item_type is not None:
            return f"list of {_TYPE_NAMES[self.item_type]}"
        return self.help or ""

    def constraints(self) -> list[str]:
        """EVERY constraint this parameter carries, for a generated table.

        `comment()` above answers a different question and answers it for
        `init`: which SINGLE constraint claims the one inline comment a config
        line has room for. A documentation table has a column of its own, so it
        prints the whole set — a `float` that is required, bounded on both
        sides and drawn from a closed set says all three or says less than it
        knows.

        `required` and `nullable` are in the list even though neither is in the
        closed constraint vocabulary `docs/reference.md` § Templates tabulates:
        both constrain what a config may write, they are what a reader of this
        table needs first, and `docs/reference.md` § Templates' own generated
        example puts `required` in exactly this column. `requires_env` travels
        inside the `choices` label, where `_choice_label` already puts it,
        because it belongs to one choice rather than to the parameter.
        """
        parts: list[str] = []
        if self.required:
            parts.append("required")
        if self.nullable:
            parts.append("nullable")
        if self.choices is not None:
            parts.append("choices: " + " | ".join(self._choice_label(c) for c in self.choices))
        for bound, sym in ((self.ge, ">="), (self.gt, ">"), (self.le, "<="), (self.lt, "<")):
            if bound is not None:
                parts.append(f"{sym} {bound}")
        if self.pattern is not None:
            parts.append(f"matches {self.pattern}")
        if self.type_ is list and self.item_type is not None:
            parts.append(f"list of {_TYPE_NAMES[self.item_type]}")
        if self.min_items is not None:
            parts.append(f"at least {self.min_items} items")
        if self.max_items is not None:
            parts.append(f"at most {self.max_items} items")
        return parts

    def type_name(self) -> str:
        """This parameter's type as core's own messages spell it.

        Read from `_TYPE_NAMES`, the mapping every `check()` message already
        interpolates, rather than from a second table in the renderer: two
        spellings of one type is how a generated document comes to disagree
        with the diagnostic a reader gets when they write the wrong one.
        """
        return _TYPE_NAMES[self.type_]

    def _choice_label(self, choice: Any) -> str:
        needs = (self.requires_env or {}).get(choice) or []
        if not needs:
            return str(choice)
        return f"{choice} (needs {', '.join(needs)})"
