# src/publishable/apparatus.py
"""What a probe returns, and how a declared probe name resolves to one.

docs/reference.md § The apparatus core can only observe and § The apparatus
files. A probe is a plain function, `probe(cfg) -> Apparatus`, registered the
same way a resolver is — `reference.md` § Creating a plugin — and `Apparatus`
is the one shape it may return.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Apparatus:
    """What a probe returns: `facts`, and nothing else.

    § The importable surface's row says "What a probe returns: facts", and a
    second field would be a surface no document describes.

    **Not validated here.** `Apparatus` is constructed inside the probe's own
    body, so a refusal raised in `__init__` would be indistinguishable from any
    other exception a probe's body raises — and would be reported as
    `E-APPARATUS-RAISED`, a code whose § Errors row describes a different
    fault. `Unit` is the shipped precedent for exactly this split: it freezes
    its attributes and validates nothing, and `units._from_resolver` is where a
    yielded non-`Unit` is refused, under `E-RESOLVER-YIELD`. The value contract
    for `facts` — `str` keys, scalar values — is enforced the same way, at
    core's boundary, once a probe has already returned.
    """

    facts: Mapping[str, Any] = field(default_factory=dict)
