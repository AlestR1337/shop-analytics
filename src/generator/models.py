from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class User:
    user_id: int
    city: str
    registered_at: datetime


@dataclass(frozen=True, slots=True)
class Product:
    product_id: int
    name: str
    category: str
    price: Decimal


@dataclass(frozen=True, slots=True)
class Order:
    order_id: int
    timestamp: datetime
    user_id: int
    product_id: int
    product: str
    category: str
    price: Decimal
    quantity: int
    city: str
    is_anomaly: bool = False
  