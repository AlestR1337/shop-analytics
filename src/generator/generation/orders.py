from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from decimal import Decimal

from generator.models import Order, Product, User
from .anomalies import AnomalyKind, AnomalyPolicy
from .metrics import OrderContext, QuantitySampler
from .seasonality import demand_factor


_CATEGORY_WEIGHTS = {
    "Одежда": 15,
    "Красота и уход": 15,
    "Дом и сад": 12,
    "Обувь": 10,
    "Электроника": 8,
    "Детские товары": 8,
    "Зоотовары": 6,
    "Аксессуары": 6,
    "Бытовая техника": 6,
    "Книги и канцелярия": 5,
    "Спорт": 5,
    "Автотовары": 4,
}


_PRODUCT_DEMAND = {
    # Товары регулярного потребления
    "Шампунь": 10,
    "Гель для душа": 10,
    "Зубная паста": 10,
    "Подгузники": 10,
    "Влажные салфетки детские": 9,
    "Дезодорант": 8,
    "Мыло жидкое": 8,
    "Сухой корм для кошек 2 кг": 10,
    "Сухой корм для собак 3 кг": 10,
    "Влажный корм для кошек": 10,
    "Влажный корм для собак": 10,
    "Наполнитель для лотка": 9,

    # Популярные повседневные товары
    "Футболка": 8,
    "Носки": 10,
    "Джинсы": 6,
    "Худи": 6,
    "Кроссовки": 7,
    "Кеды": 6,
    "Наушники": 6,
    "Беспроводные наушники": 6,
    "Кабель USB-C": 8,
    "Зарядное устройство USB-C": 7,
    "Смартфон": 4,
    "Бюджетный смартфон": 5,
    "Крем для рук": 7,
    "Полотенце": 6,
    "Шариковая ручка": 7,
    "Бумага A4": 7,

    # Товары длительного использования
    "Ноутбук": 2,
    "Игровой ноутбук": 1,
    "Миксер": 1,
    "Холодильник": 1,
    "Стиральная машина": 1,
    "Посудомоечная машина": 1,
    "Кофемашина": 1,
    "Пылесос": 2,
    "Боксёрские перчатки": 1,
    "Беговая дорожка": 1,
    "Велотренажёр": 1,
    "Горный велосипед": 1,
    "Аквариум 40 л": 1,
    "Детская коляска": 1,
    "Письменный стол": 1,
    "Офисное кресло": 2,
}


def _build_product_weights(
    products: list[Product],
    rng: random.Random,
) -> list[float]:
    """Рассчитать веса товаров с учётом спроса и цены."""

    weights = []
    category_totals = {}

    for product in products:
        demand = _PRODUCT_DEMAND.get(product.name, 3)

        price_factor = (
            3 if product.price < Decimal("5000")
            else 2 if product.price < Decimal("20000")
            else 1
        )

        variation = rng.uniform(0.85, 1.15)

        weight = demand * price_factor * variation

        weights.append(weight)

        category_totals[product.category] = (
            category_totals.get(product.category, 0)
            + weight
        )

    return [
        weight
        / category_totals[product.category]
        * _CATEGORY_WEIGHTS.get(product.category, 1)
        for product, weight in zip(products, weights)
    ]


class OrderGenerator:
    """Генерация заказов одного пользователя."""

    def __init__(
        self,
        user: User,
        products: list[Product],
        anomaly_policy: AnomalyPolicy,
        rng: random.Random,
        product_weights: list[float] | None = None,
    ) -> None:
        if not products:
            raise ValueError("Каталог товаров пуст")

        self._user = user
        self._products = products
        self._anomaly_policy = anomaly_policy
        self._rng = rng
        self._quantity = QuantitySampler()
        self._product_weights = (
            product_weights
            if product_weights is not None
            else _build_product_weights(products, rng)
        )

    @property
    def user(self) -> User:
        return self._user

    def generate(self, at: datetime, order_id: int) -> Order:
        """Создать один заказ."""

        anomaly = self._anomaly_policy.decide()

        product = self._choose_product(anomaly)

        ctx = OrderContext(product=product)

        quantity = self._quantity.sample(ctx, self._rng)

        quantity = self._apply_quantity_anomaly(
            quantity, anomaly
        )

        return Order(
            order_id=order_id,
            timestamp=at,
            user_id=self._user.user_id,
            product_id=product.product_id,
            product=product.name,
            category=product.category,
            price=product.price,
            quantity=quantity,
            city=self._user.city,
            is_anomaly=anomaly is not None,
        )

    def _choose_product(
        self,
        anomaly: AnomalyKind | None,
    ) -> Product:
        """Выбор товара с учётом аномалии."""

        rng = self._rng

        if anomaly == AnomalyKind.BULK_ORDER:
            cheap = [
                p for p in self._products
                if p.price < Decimal("5000")
            ]
            return rng.choice(cheap or self._products)

        if anomaly == AnomalyKind.HIGH_VALUE_ORDER:
            expensive = [
                p for p in self._products
                if p.price >= Decimal("20000")
            ]

            if expensive:
                return rng.choice(expensive)

            return max(
                self._products,
                key=lambda p: p.price,
            )

        # Обычные покупки с учётом цены и популярности
        return rng.choices(
            self._products,
            weights=self._product_weights,
            k=1,
        )[0]

    def _apply_quantity_anomaly(
        self,
        quantity: int,
        anomaly: AnomalyKind | None,
    ) -> int:
        """Изменить количество при аномалии."""

        strength = self._anomaly_policy.strength

        if anomaly == AnomalyKind.BULK_ORDER:
            multiplier = self._rng.uniform(2.0, 4.0)

            return max(
                10,
                math.ceil(quantity * strength * multiplier),
            )

        if anomaly == AnomalyKind.HIGH_VALUE_ORDER:
            return max(
                2,
                math.ceil(quantity * strength),
            )

        return quantity


class BatchGenerator:
    """Производит пачку заказов покупателей за окно времени.

    Каждая запись последовательности получает свой момент времени.
    Шаг между заказами зависит от суточной и недельной активности покупателей.
    Заказы распределяются между пользователями с учётом их активности.
    """

    def __init__(
        self,
        users: list[User],
        products: list[Product],
        seed: int,
        anomaly_policy: AnomalyPolicy,
    ) -> None:
        if not users:
            raise ValueError("Список пользователей пуст")

        if not products:
            raise ValueError("Каталог товаров пуст")

        self._products = products
        self._rng = random.Random(seed)
        profile_rng = random.Random(seed + 1)

        product_weights = _build_product_weights(
            products,
            profile_rng,
        )

        self._per_user = [
            OrderGenerator(
                user,
                products,
                anomaly_policy,
                self._rng,
                product_weights,
            )
            for user in users
        ]

        self._user_weights = profile_rng.choices(
            [1, 3, 8],
            weights=[60, 30, 10],
            k=len(users),
        )

        self._next_order_id = 1

    @property
    def users(self) -> list[User]:
        return [g.user for g in self._per_user]

    @property
    def products(self) -> list[Product]:
        return list(self._products)

    def set_next_order_id(self, order_id: int) -> None:
        """Установить идентификатор следующего заказа."""
        if order_id < 1:
            raise ValueError("Идентификатор заказа должен быть положительным")

        self._next_order_id = order_id

    def generate_batch(
        self,
        at: datetime,
        size: int,
    ) -> list[Order]:
        """Создать пачку заказов."""

        if size < 0:
            raise ValueError("Размер батча не может быть отрицательным")

        orders: list[Order] = []

        for _ in range(size):
            generator = self._rng.choices(
                self._per_user,
                weights=self._user_weights,
                k=1,
            )[0]

            order = generator.generate(
                at,
                self._next_order_id,
            )

            orders.append(order)

            self._next_order_id += 1

        return orders

    def next_timestamp(
        self,
        at: datetime,
        step_seconds: float,
    ) -> datetime:
        """Следующий момент генерации с учётом сезонности."""
        if step_seconds <= 0:
            raise ValueError("Шаг генерации должен быть положительным")

        step = max(0.1, step_seconds / demand_factor(at))

        return at + timedelta(seconds=step)

    def generate_sequence(
        self,
        start: datetime,
        count: int,
        step_seconds: float,
        end: datetime | None = None,
    ) -> list[Order]:
        """Прямая последовательность заказов, начиная с `start`.

        Используется бэкфиллом и realtime-фазой: каждая запись получает свой,
        возрастающий таймстемп с учётом сезонности.
        Если задан `end`, генерация не выходит за пределы этого времени.
        """
        if count < 0:
            raise ValueError("Количество заказов не может быть отрицательным")

        if step_seconds <= 0:
            raise ValueError("Шаг генерации должен быть положительным")

        orders: list[Order] = []
        ts = start

        for _ in range(count):
            if end is not None and ts > end:
                break

            orders.extend(self.generate_batch(ts, 1))
            ts = self.next_timestamp(ts, step_seconds)

        return orders