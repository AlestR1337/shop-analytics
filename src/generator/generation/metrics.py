"""Самплеры метрик (паттерн Strategy).

Каждая метрика — отдельный класс-стратегия с единым контрактом
``sample(ctx, rng) -> float``. ``WeatherReadingGenerator`` комбинирует стратегии,
поэтому добавить новую метрику = написать один класс и зарегистрировать его —
существующие не меняются (принцип открытости/закрытости, OCP).
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from .seasonality import annual_factor, diurnal_factor


@dataclass(frozen=True, slots=True)
class ClimateProfile:
    """Климатические параметры станции — «фон» для генерации значений."""

    mean_annual_temp_c: float
    annual_temp_amplitude_c: float
    daily_temp_amplitude_c: float
    humidity_base_pct: float
    pressure_base_hpa: float = 1013.25
    wind_base_ms: float = 4.0


@dataclass(frozen=True, slots=True)
class ReadingContext:
    """Контекст, общий для самплеров одного показания.

    Содержит момент времени и уже посчитанную температуру, чтобы
    влажность/давление могли коррелировать с ней (реалистичная динамика).
    """

    at: datetime
    temperature_c: float


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class MetricSampler(ABC):
    """Базовый контракт стратегии: вернуть значение метрики для контекста."""

    @abstractmethod
    def sample(self, ctx: ReadingContext, rng: random.Random) -> float: ...


class TemperatureSampler(MetricSampler):
    """Температура = климат + годовая/суточная сезонность + шум."""

    def __init__(self, profile: ClimateProfile, noise_std: float = 1.2) -> None:
        self._profile = profile
        self._noise_std = noise_std

    def sample(self, ctx: ReadingContext, rng: random.Random) -> float:
        base = (
            self._profile.mean_annual_temp_c
            + self._profile.annual_temp_amplitude_c * annual_factor(ctx.at)
            + self._profile.daily_temp_amplitude_c * diurnal_factor(ctx.at)
        )
        return round(base + rng.gauss(0.0, self._noise_std), 2)


class HumiditySampler(MetricSampler):
    """Влажность обратно коррелирует с температурой, шум слабее."""

    def __init__(self, profile: ClimateProfile) -> None:
        self._profile = profile

    def sample(self, ctx: ReadingContext, rng: random.Random) -> float:
        deviation = ctx.temperature_c - self._profile.mean_annual_temp_c
        value = self._profile.humidity_base_pct - 0.8 * deviation + rng.gauss(0.0, 3.0)
        return round(_clamp(value, 5.0, 100.0), 2)


class PressureSampler(MetricSampler):
    """Давление: базовое + слабый суточный «прилив» + шум."""

    def __init__(self, profile: ClimateProfile, tide_amplitude: float = 1.2) -> None:
        self._profile = profile
        self._tide_amplitude = tide_amplitude

    def sample(self, ctx: ReadingContext, rng: random.Random) -> float:
        tide = self._tide_amplitude * diurnal_factor(ctx.at)
        value = self._profile.pressure_base_hpa + tide + rng.gauss(0.0, 0.8)
        return round(_clamp(value, 850.0, 1100.0), 2)


class WindSpeedSampler(MetricSampler):
    """Скорость ветра: асимметричное распределение (чаще тихо, реже порывы)."""

    def __init__(self, profile: ClimateProfile) -> None:
        self._profile = profile

    def sample(self, ctx: ReadingContext, rng: random.Random) -> float:
        # log-normal: неотрицательная асимметричная величина вокруг базового уровня.
        value = self._profile.wind_base_ms * rng.lognormvariate(0.0, 0.55)
        return round(_clamp(value, 0.0, 60.0), 2)


class WindDirectionSampler(MetricSampler):
    """Направление ветра в градусах [0, 360) с медленным блужданием."""

    def __init__(self, profile: ClimateProfile, step_deg: float = 15.0) -> None:
        self._profile = profile
        self._step_deg = step_deg

    def sample(self, ctx: ReadingContext, rng: random.Random) -> float:
        value = rng.uniform(0.0, 360.0)
        return round(value, 1)
