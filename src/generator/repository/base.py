
"""Интерфейс хранилища данных интернет-магазина."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from generator.models import Order, Product, User


class Repository(Protocol):
    """Контракт для всех реализаций хранилища."""

    def ensure_schema(self) -> None:
        """Подготовить структуру хранилища."""
        ...

    def upsert_users(self, users: list[User]) -> None:
        """Добавить или обновить пользователей."""
        ...

    def upsert_products(self, products: list[Product]) -> None:
        """Добавить или обновить товары."""
        ...

    def insert_orders(self, orders: list[Order]) -> None:
        """Добавить новые заказы."""
        ...

    def max_timestamp(self) -> datetime | None:
        """Получить время последнего заказа."""
        ...
