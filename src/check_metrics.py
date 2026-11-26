import random

from generator.generation.catalog import ProductCatalog
from generator.generation.metrics import (
    OrderContext,
    QuantitySampler,
    calculate_order_total,
)


rng = random.Random(42)

products = ProductCatalog().products()
sampler = QuantitySampler()

for product in products:
    ctx = OrderContext(product=product)

    quantity = sampler.sample(ctx, rng)
    total = calculate_order_total(product, quantity)

    print(
        f"{product.name}: "
        f"{quantity} шт. — {total} руб."
    )