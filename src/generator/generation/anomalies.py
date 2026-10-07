"""Политика редких аномалий/выбросов.

Аномалии нужны как «дрожжи» для последующего анализа: студенты должны найти их
в Jupyter. Здесь аномалия — это **тип** отклонения, а конкретная величина
(сила скачка) вычисляется в генераторе показаний на основе ``anomaly_strength``.
"""

from __future__ import annotations

import enum
import random


class AnomalyKind(enum.StrEnum):
    """Типы аномалий, которые может генерировать система."""

    HEAT_WAVE = "heat_wave"  # резкий скачок температуры вверх
    COLD_SNAP = "cold_snap"  # резкий скачок температуры вниз
    PRESSURE_DROP = "pressure_drop"  # резкое падение давления (признак бури)
    WIND_GUST = "wind_gust"  # порыв ветра


class AnomalyPolicy:
    """Решает, случится ли аномалия в текущем показании и какая именно."""

    def __init__(self, probability: float, strength: float, rng: random.Random) -> None:
        self._probability = probability
        self._strength = strength
        self._rng = rng

    @property
    def strength(self) -> float:
        """Сила аномалии (множитель), настраивается извне."""
        return self._strength

    def decide(self) -> AnomalyKind | None:
        """Возвращает тип аномалии для текущей записи или ``None``."""
        if self._rng.random() >= self._probability:
            return None
        return self._rng.choice(list(AnomalyKind))
