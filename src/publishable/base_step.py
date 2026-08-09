"""One stage of the pipeline. `__init__` is core's — don't define one."""

import hashlib
import random
from typing import Any

from publishable.errors import ContractError


class BaseStep:
    scope: str = "repeat"
    nondeterministic: bool = False

    def __init__(self) -> None:
        self._condition: Any = None
        self._repeat: str | None = None
        self._digest: str = ""
        self._seed: int = 0
        self.rng: random.Random = random.Random(0)

    def _bind(self, *, condition: Any, repeat: str | None, digest: str, seed: int) -> None:
        """Core sets the execution context before calling `run`."""
        self._condition = condition
        self._repeat = repeat
        self._digest = digest
        self._seed = seed
        self.rng = random.Random(seed)

    @property
    def condition(self) -> Any:
        if self._condition is None:
            raise ContractError(
                f"`self.condition` has no value at scope {self.scope!r}",
                code="E-STEP-CONTEXT-ABSENT",
            )
        return self._condition

    @property
    def repeat(self) -> str:
        if self._repeat is None:
            raise ContractError(
                f"`self.repeat` has no value at scope {self.scope!r}",
                code="E-STEP-CONTEXT-ABSENT",
            )
        return self._repeat

    def derive_seed(self, purpose: str) -> int:
        """Mix the design digest, the execution seed, and the purpose into an integer."""
        payload = f"{self._digest}|{self._seed}|{purpose}".encode()
        return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")

    def run(self, cfg: Any, io: Any) -> dict[str, Any]:
        raise NotImplementedError
