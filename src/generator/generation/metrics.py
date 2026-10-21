
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from generator.models import Product


@dataclass(frozen=True, slots=True)
class OrderContext:
    """Контекст для генерации метрик заказа."""
    product: Product


class MetricSampler(ABC):
    """Общий интерфейс для генерации метрик."""

    @abstractmethod
    def sample(
        self,
        ctx: OrderContext,
        rng: random.Random,
    ) -> int:
        ...


class QuantitySampler(MetricSampler):
    """Генерация количества товаров в заказе."""

    def sample(
        self,
        ctx: OrderContext,
        rng: random.Random,
    ) -> int:

        price = ctx.product.price
        quantities = [1, 2, 3, 4, 5]

        if price < Decimal("5000"):
            weights = [55, 25, 12, 6, 2]

        elif price < Decimal("20000"):
            weights = [75, 18, 6, 1, 0]

        else:
            weights = [90, 9, 1, 0, 0]

        return rng.choices(
            quantities,
            weights=weights,
            k=1,
        )[0]


def calculate_order_total(
    product: Product,
    quantity: int,
) -> Decimal:
    """Рассчитать стоимость покупки."""

    if quantity <= 0:
        raise ValueError("Количество должно быть больше нуля")

    return product.price * quantity
