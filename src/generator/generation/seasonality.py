
from __future__ import annotations

import math
from datetime import datetime


def diurnal_factor(at: datetime) -> float:
    """Суточная активность покупателей от -1 до 1."""

    hour = (
        at.hour
        + at.minute / 60.0
        + at.second / 3600.0
    )

    # Максимум в 16:00, минимум в 04:00
    return math.cos(
        2.0 * math.pi * (hour - 16.0) / 24.0
    )


def weekly_factor(at: datetime) -> float:
    """Повышенная активность в выходные."""

    if at.weekday() >= 5:
        return 1.15

    return 1.0


def demand_factor(at: datetime) -> float:
    """Общий коэффициент интенсивности заказов."""

    daily = 1.0 + 0.7 * diurnal_factor(at)
    weekly = weekly_factor(at)

    return daily * weekly
