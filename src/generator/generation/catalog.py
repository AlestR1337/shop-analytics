
from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal

from generator.models import Product, User


# Шаблоны товаров
_PRODUCTS = [
    ("Смартфон", "Электроника", "39990.00"),
    ("Ноутбук", "Электроника", "79990.00"),
    ("Наушники", "Электроника", "4990.00"),
    ("Футболка", "Одежда", "1490.00"),
    ("Куртка", "Одежда", "8990.00"),
    ("Кроссовки", "Обувь", "6990.00"),
    ("Ботинки", "Обувь", "9990.00"),
    ("Кофемашина", "Бытовая техника", "24990.00"),
    ("Пылесос", "Бытовая техника", "15990.00"),
]


class ProductCatalog:
    """Справочник товаров интернет-магазина."""

    def products(self) -> list[Product]:
        return [
            Product(
                product_id=index,
                name=name,
                category=category,
                price=Decimal(price),
            )
            for index, (name, category, price)
            in enumerate(_PRODUCTS, start=1)
        ]


class UserCatalog:
    """Генератор справочника пользователей."""

    def __init__(
        self,
        cities: list[str],
        count: int,
        seed: int,
        as_of: datetime,
    ) -> None:
        if not cities:
            raise ValueError("Список городов пуст")

        if count <= 0:
            raise ValueError("Количество пользователей должно быть положительным")

        self._cities = cities
        self._count = count
        self._seed = seed
        self._as_of = as_of

    def users(self) -> list[User]:
        rng = random.Random(self._seed)

        return [
            User(
                user_id=index,
                city=rng.choice(self._cities),
                registered_at=(
                    self._as_of
                    - timedelta(days=rng.randint(1, 730))
                ),
            )
            for index in range(1, self._count + 1)
        ]
