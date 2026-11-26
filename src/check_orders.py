import random
from datetime import datetime

from generator.generation.catalog import (
    ProductCatalog,
    UserCatalog,
)
from generator.generation.anomalies import AnomalyPolicy
from generator.generation.orders import BatchGenerator
from generator.generation.metrics import calculate_order_total


at = datetime(2026, 10, 20, 18, 0)

products = ProductCatalog().products()

users = UserCatalog(
    cities=["Moscow", "Kazan", "Vladivostok"],
    count=20,
    seed=42,
    as_of=at,
).users()

policy = AnomalyPolicy(
    probability=0.02,
    strength=3.0,
    rng=random.Random(123),
)

generator = BatchGenerator(
    users=users,
    products=products,
    seed=42,
    anomaly_policy=policy,
)

# Генерируем две пачки
batch1 = generator.generate_batch(at, 50)
batch2 = generator.generate_batch(at, 50)

orders = batch1 + batch2

for order in orders[:10]:
    total = calculate_order_total(
        products[order.product_id - 1],
        order.quantity,
    )

    print(
        f"Заказ №{order.order_id} | "
        f"{order.product} | "
        f"{order.quantity} шт. | "
        f"{total} руб. | "
        f"Аномалия: {order.is_anomaly}"
    )

print("\nВсего заказов:", len(orders))
print(
    "Аномальных:",
    sum(order.is_anomaly for order in orders),
)

assert len(orders) == 100
assert [o.order_id for o in orders] == list(range(1, 101))

# Проверка уникальности идентификаторов
order_ids = [order.order_id for order in orders]

assert len(order_ids) == len(set(order_ids))

# Проверка количества товаров
assert all(order.quantity > 0 for order in orders)

# Проверка связей с пользователями и товарами
user_ids = {user.user_id for user in users}
product_ids = {product.product_id for product in products}

assert all(order.user_id in user_ids for order in orders)
assert all(order.product_id in product_ids for order in orders)

print("Все проверки успешно пройдены!")