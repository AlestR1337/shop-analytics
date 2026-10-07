"""Доменные модели предметной области «погодная станция».

Модели — «чистые» объекты без знания о БД и способе генерации. Это ядро
домена, вокруг которого строятся остальные слои (генерация, репозитории, сервис).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime


class WeatherType(enum.StrEnum):
    """Категория погоды — поле-размерность для последующей аналитики."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    FOG = "fog"
    RAIN = "rain"
    SNOW = "snow"
    STORM = "storm"


@dataclass(frozen=True, slots=True)
class Station:
    """Справочная запись метеостанции (справочник/измерение)."""
    station_id: int
    name: str
    city: str
    latitude: float
    longitude: float
    altitude: float  # метры над уровнем моря


@dataclass(frozen=True, slots=True)
class WeatherReading:
    """Показание метеостанции в конкретный момент времени (событие).

    Поля:
      * размерности — ``weather_type``, ``wind_direction_deg``;
      * метрики     — ``temperature_c``, ``humidity_pct``, ``pressure_hpa``,
        ``wind_speed_ms``;
      * флаг ``is_anomaly`` помечает редкие выбросы для последующего анализа.
    """

    station_id: int
    timestamp: datetime
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    wind_speed_ms: float
    wind_direction_deg: float
    weather_type: WeatherType
    is_anomaly: bool
