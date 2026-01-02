from pathlib import Path
from typing import Iterable
from .models import Signal
from .layer_signal import detect_sensitive_layer
from .size_signal import detect_large_functions
from .complexity_signal import detect_complex_functions


def collect_signals(files: Iterable[Path]) -> list[Signal]:
    """
    Collect all architectural signals from given files.
    Pure domain logic – no filtering, no policy.
    """
    signals: list[Signal] = []

    for f in files:
        signals.extend(detect_sensitive_layer(f))
        signals.extend(detect_large_functions(f))
        signals.extend(detect_complex_functions(f))

    return signals
