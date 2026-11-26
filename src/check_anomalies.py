import random
from collections import Counter

from generator.generation.anomalies import (
    AnomalyKind,
    AnomalyPolicy,
)


rng = random.Random(42)

policy = AnomalyPolicy(
    probability=0.02,
    strength=3.0,
    rng=rng,
)

counts = Counter()

for _ in range(1000):
    anomaly = policy.decide()

    if anomaly is None:
        counts["normal"] += 1
    else:
        counts[anomaly.value] += 1


print("Обычных:", counts["normal"])
print("Массовых покупок:", counts["bulk_order"])
print("Дорогих заказов:", counts["high_value_order"])
print("Сила аномалий:", policy.strength)