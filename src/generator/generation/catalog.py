"""Справочник станций и их климатических профилей.

Отделяет «что генерировать» (климат города) от «как генерировать» (самплеры).
``StationCatalog`` создаёт N станций с реалистичными координатами и профилями.
"""

from __future__ import annotations

from dataclasses import dataclass

from generator.models import Station

from .metrics import ClimateProfile

_GENERIC = ClimateProfile(
    mean_annual_temp_c=10.0,
    annual_temp_amplitude_c=20.0,
    daily_temp_amplitude_c=7.0,
    humidity_base_pct=70.0,
)


@dataclass(frozen=True, slots=True)
class _Template:
    city: str
    latitude: float
    longitude: float
    altitude: float
    climate: ClimateProfile


_TEMPLATES: dict[str, _Template] = {
    "Vladivostok": _Template(
        "Vladivostok", 43.12, 131.89, 40,
        ClimateProfile(mean_annual_temp_c=4.8, annual_temp_amplitude_c=22.0,
                       daily_temp_amplitude_c=6.0, humidity_base_pct=76.0,
                       pressure_base_hpa=1012.0, wind_base_ms=6.0),
    ),
    "Moscow": _Template(
        "Moscow", 55.76, 37.62, 156,
        ClimateProfile(mean_annual_temp_c=6.0, annual_temp_amplitude_c=25.0,
                       daily_temp_amplitude_c=7.0, humidity_base_pct=72.0,
                       pressure_base_hpa=1013.0, wind_base_ms=5.0),
    ),
    "Kazan": _Template(
        "Kazan", 55.79, 49.12, 64,
        ClimateProfile(mean_annual_temp_c=4.5, annual_temp_amplitude_c=27.0,
                       daily_temp_amplitude_c=7.0, humidity_base_pct=73.0,
                       pressure_base_hpa=1013.0, wind_base_ms=4.5),
    ),
    "Sochi": _Template(
        "Sochi", 43.60, 39.73, 30,
        ClimateProfile(mean_annual_temp_c=14.0, annual_temp_amplitude_c=14.0,
                       daily_temp_amplitude_c=6.0, humidity_base_pct=75.0,
                       pressure_base_hpa=1012.0, wind_base_ms=3.0),
    ),
    "Irkutsk": _Template(
        "Irkutsk", 52.29, 104.28, 444,
        ClimateProfile(mean_annual_temp_c=1.0, annual_temp_amplitude_c=33.0,
                       daily_temp_amplitude_c=9.0, humidity_base_pct=68.0,
                       pressure_base_hpa=1005.0, wind_base_ms=4.0),
    ),
}


class StationCatalog:
    """Фабрика станций по списку городов из конфигурации."""

    def __init__(self, cities: list[str]) -> None:
        self._templates = [self._resolve(city) for city in cities]

    @staticmethod
    def _resolve(city: str) -> _Template:
        # Неизвестный город получает обобщённый профиль, чтобы система не падала.
        return _TEMPLATES.get(city, _Template(city, 0.0, 0.0, 100.0, _GENERIC))

    def stations(self) -> list[Station]:
        return [
            Station(
                station_id=index,
                name=f"{t.city} Station",
                city=t.city,
                latitude=t.latitude,
                longitude=t.longitude,
                altitude=t.altitude,
            )
            for index, t in enumerate(self._templates)
        ]

    def climate_for(self, station: Station) -> ClimateProfile:
        return next(t.climate for t in self._templates if t.city == station.city)
