"""metrics package: simple evaluation utilities."""

from typing import Sequence


def accuracy(preds: Sequence[int], labels: Sequence[int]) -> float:
    """Compute simple accuracy.

    This is a placeholder implementation.
    """
    if not preds:
        return 0.0
    correct = sum(p == l for p, l in zip(preds, labels))
    return correct / len(preds)
