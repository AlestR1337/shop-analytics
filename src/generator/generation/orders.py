
from __future__ import annotations

import math
import random
from datetime import datetime
from decimal import Decimal

from generator.models import Order, Product, User
from .anomalies import AnomalyKind, AnomalyPolicy
from .metrics import OrderContext, QuantitySampler


class OrderGenerator:
    """Генерация заказов одного пользователя."""

    def __init__(
        self,
        user: User,
        products: list[Product],
        anomaly_policy: AnomalyPolicy,
        rng: random.Random,
    ) -> None:
        if not products:
            raise ValueError("Каталог товаров пуст")

        self._user = user
        self._products = products
        self._anomaly_policy = anomaly_policy
        self._rng = rng
        self._quantity = QuantitySampler()

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

        # Обычные покупки: дешёвые товары популярнее
        weights = [
            3 if p.price < Decimal("5000")
            else 2 if p.price < Decimal("20000")
            else 1
            for p in self._products
        ]

        return rng.choices(
            self._products,
            weights=weights,
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
    """Генерация пачки заказов."""

    def __init__(
        self,
        users: list[User],
        products: list[Product],
        seed: int,
        anomaly_policy: AnomalyPolicy,
    ) -> None:
        if not users:
            raise ValueError("Список пользователей пуст")

        rng = random.Random(seed)

        self._per_user = [
            OrderGenerator(
                user,
                products,
                anomaly_policy,
                rng,
            )
            for user in users
        ]

        self._next_user = 0
        self._next_order_id = 1

    @property
    def users(self) -> list[User]:
        return [g.user for g in self._per_user]

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
            generator = self._per_user[
                self._next_user % len(self._per_user)
            ]

            order = generator.generate(
                at,
                self._next_order_id,
            )

            orders.append(order)

            self._next_user += 1
            self._next_order_id += 1

        return orders
