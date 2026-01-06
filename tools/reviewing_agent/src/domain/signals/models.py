from dataclasses import dataclass
from typing import Literal

SignalType = Literal[
    "SENSITIVE_LAYER",
    "LARGE_FUNCTION",
    "HIGH_COMPLEXITY",
    "CROSS_LAYER_CALL",
]

@dataclass
class Signal:
    type: SignalType
    file: str
    function: str | None
    score: int
    reason: str
    line: int | None
