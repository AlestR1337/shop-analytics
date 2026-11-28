"""In-memory реализация репозитория.

Нужна для юнит-тестов и локального запуска без ClickHouse: показывает
интерфейс хранилища, не требуя внешней БД.
"""

from __future__ import annotations

from datetime import datetime

from generator.models import User, Product, Order


class InMemoryRepository:
    """Хранит пользователей, товары и заказы в оперативной памяти."""

    def __init__(self) -> None:
        self.users: list[User] = []
        self.products: list[Product] = []
        self.orders: list[Order] = []

    def ensure_schema(self) -> None:
        """In-memory хранилище не требует инициализации схемы."""

    def upsert_users(self, users: list[User]) -> None:
        by_id = {u.user_id: u for u in self.users}
        for user in users:
            by_id[user.user_id] = user
        self.users = sorted(by_id.values(), key=lambda u: u.user_id)

    def upsert_products(self, products: list[Product]) -> None:
        by_id = {p.product_id: p for p in self.products}
        for product in products:
            by_id[product.product_id] = product
        self.products = sorted(by_id.values(), key=lambda p: p.product_id)

    def insert_orders(self, orders: list[Order]) -> None:
        self.orders.extend(orders)

    def max_timestamp(self) -> datetime | None:
        return max((o.timestamp for o in self.orders), default=None)

    def max_order_id(self) -> int | None:
        return max((o.order_id for o in self.orders), default=None)