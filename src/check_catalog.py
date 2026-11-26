from datetime import datetime

from generator.generation.catalog import (
    ProductCatalog,
    UserCatalog,
)

products = ProductCatalog().products()

users = UserCatalog(
    cities=["Moscow", "Kazan", "Vladivostok"],
    count=5,
    seed=42,
    as_of=datetime(2026, 10, 20),
).users()

print("Товары:")
for product in products:
    print(product)

print("\nПользователи:")
for user in users:
    print(user)

print("\nВсего товаров:", len(products))
print("Всего пользователей:", len(users))