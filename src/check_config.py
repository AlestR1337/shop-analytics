from generator.config import get_settings

settings = get_settings()

print("Количество пользователей:", settings.generator.user_count)
print("Города:", settings.generator.city_list)
print("Размер батча:", settings.generator.batch_size)
print("Интервал:", settings.generator.interval_seconds)
print("Seed:", settings.generator.seed)
print("Вероятность аномалии:", settings.generator.anomaly_probability)
print("База данных:", settings.clickhouse.database)