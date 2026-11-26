
from __future__ import annotations

import enum
import random


class AnomalyKind(enum.StrEnum):
    """Типы аномалий интернет-магазина."""

    BULK_ORDER = "bulk_order"
    HIGH_VALUE_ORDER = "high_value_order"


class AnomalyPolicy:
    """Определяет, возникнет ли аномалия и какого она типа."""

    def __init__(
        self,
        probability: float,
        strength: float,
        rng: random.Random,
    ) -> None:
        self._probability = probability
        self._strength = strength
        self._rng = rng

    @property
    def strength(self) -> float:
        """Множитель силы аномалии."""
        return self._strength

    def decide(self) -> AnomalyKind | None:
        """Возвращает тип аномалии или None."""

        if self._rng.random() >= self._probability:
            return None

        return self._rng.choice(list(AnomalyKind))
