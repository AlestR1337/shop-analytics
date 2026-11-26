from datetime import datetime

from generator.generation.seasonality import (
    demand_factor,
)


# Вторник — обычный будний день
for hour in range(0, 24, 2):
    at = datetime(2026, 10, 20, hour)

    factor = demand_factor(at)

    print(f"{hour:02d}:00 — {factor:.2f}")


print("\nСравнение буднего и выходного дня:")

weekday = datetime(2026, 10, 20, 16)
weekend = datetime(2026, 10, 24, 16)

print("Вторник:", round(demand_factor(weekday), 2))
print("Суббота:", round(demand_factor(weekend), 2))