"""Сервис генерации: бэкфилл исторических данных + realtime-дополнение.

Две фазы:
- ``backfill`` — заполняет окно от ``backfill_start`` (по умолчанию 2025-01-01)
  до текущего момента с базовым шагом ``backfill_step_seconds``. Возобновляется с
  последнего таймстемпа в хранилище.
- ``realtime`` — после достижения текущего времени продолжает генерацию заказов
  с базовым шагом ``realtime_step_seconds``.

Интенсивность генерации учитывает суточную и недельную активность покупателей.

Сервис зависит только от абстракций (Repository, BatchGenerator, RetryPolicy),
не зная деталей конкретной БД.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from generator.config import Settings
from generator.generation.orders import BatchGenerator
from generator.models import Order
from generator.repository.base import Repository
from generator.retry import RetryError, RetryPolicy


Clock = Callable[[], datetime]
logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(UTC)


class GeneratorService:
    """Основной цикл генератора: бэкфилл + realtime."""

    def __init__(
        self,
        *,
        settings: Settings,
        batch_generator: BatchGenerator,
        repository: Repository,
        retry: RetryPolicy,
        stop_event: threading.Event,
        clock: Clock = utc_now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._batch_generator = batch_generator
        self._repository = repository
        self._retry = retry
        self._stop_event = stop_event
        self._clock = clock
        self._sleep = sleep

    # --- Публичный цикл ------------------------------------------------------

    def run(self) -> None:
        """Запускает генерацию до сигнала остановки."""
        try:
            self._initialize()
            self._backfill()
            self._run_realtime()
        except RetryError as exc:
            logger.error("Запись данных не удалась: %s", exc)
        finally:
            logger.info("Генератор остановлен.")

    def run_once(self) -> None:
        """Инициализирует схему, пишет справочники и один батч заказов."""
        self._initialize()

        g = self._settings.generator
        ts = self._get_next_timestamp(g.backfill_step_seconds)

        batch = self._batch_generator.generate_sequence(
            ts, g.batch_size, g.backfill_step_seconds, end=self._clock()
        )

        self._store(batch)
        logger.info("Один батч записан: %d заказов, завершение.", len(batch))

    # --- Фазы ----------------------------------------------------------------

    def _backfill(self) -> None:
        g = self._settings.generator
        start = g.backfill_start_dt
        step = g.backfill_step_seconds
        batch_size = g.batch_size
        now = self._clock()

        next_ts = self._get_next_timestamp(step)
        total_span = max((now - start).total_seconds(), 1.0)
        produced = 0

        while next_ts <= now and not self._stop_event.is_set():
            # Не заходим за `now`: последний батч обрезаем до оставшегося окна,
            # иначе появятся записи с будущими таймстемпами и realtime застрянет,
            # ожидая, пока реальное время догонит перескоченный `next_ts`.
            batch = self._batch_generator.generate_sequence(
                next_ts, batch_size, step, end=now
            )

            if not batch:
                break

            self._store(batch)
            produced += len(batch)

            next_ts = self._batch_generator.next_timestamp(
                batch[-1].timestamp, step
            )

            progress = min(100.0, (next_ts - start).total_seconds() / total_span * 100.0)

            if produced % (batch_size * 20) == 0:
                logger.info("Бэкфилл: до %s (%d строк, %.1f%%)", next_ts, produced, progress)

        logger.info("Бэкфилл завершён: %d строк, следующий заказ в %s", produced, next_ts)

    def _run_realtime(self) -> None:
        g = self._settings.generator
        step = g.realtime_step_seconds
        next_ts = self._get_next_timestamp(step)

        while not self._stop_event.is_set():
            now = self._clock()

            if next_ts > now:
                # Ждём, пока реальное время достигнет таймстемпа следующего заказа.
                self._sleep(min(1.0, (next_ts - now).total_seconds()))
                continue

            batch = self._batch_generator.generate_sequence(next_ts, 1, step)
            self._store(batch)

            next_ts = self._batch_generator.next_timestamp(
                batch[-1].timestamp, step
            )

    # --- Внутренние шаги ------------------------------------------------------

    def _initialize(self) -> None:
        """Подготовить хранилище, справочники и нумерацию заказов."""
        start = self._settings.generator.backfill_start_dt

        if any(user.registered_at > start for user in self._batch_generator.users):
            raise ValueError("Дата регистрации пользователя позже начала бэкфилла")

        logger.info("Инициализация схемы и справочников...")
        self._retry.execute(self._repository.ensure_schema)

        self._write_catalogs()

        last_id = self._retry.execute(self._repository.max_order_id)
        self._batch_generator.set_next_order_id((last_id or 0) + 1)

        logger.info("Пользователи записаны: %d.", len(self._batch_generator.users))
        logger.info("Товары записаны: %d.", len(self._batch_generator.products))

    def _get_next_timestamp(self, step: float) -> datetime:
        """Определить следующий таймстемп с учётом сохранённых заказов."""
        start = self._settings.generator.backfill_start_dt
        last = self._retry.execute(self._repository.max_timestamp)

        if last is not None and last >= start:
            return self._batch_generator.next_timestamp(last, step)

        return start

    def _write_catalogs(self) -> None:
        users = self._batch_generator.users
        products = self._batch_generator.products

        self._retry.execute(lambda: self._repository.upsert_users(users))
        self._retry.execute(lambda: self._repository.upsert_products(products))

    def _store(self, batch: list[Order]) -> None:
        if batch:
            self._retry.execute(lambda: self._repository.insert_orders(batch))


def build_service(
    *,
    settings: Settings,
    batch_generator: BatchGenerator,
    repository: Repository,
    stop_event: threading.Event,
) -> GeneratorService:
    """Композиционный корень: собирает сервис с политикой retry из настроек."""
    retry = RetryPolicy(
        max_attempts=settings.generator.retry_max_attempts,
        base_delay=settings.generator.retry_base_delay_seconds,
        max_delay=settings.generator.retry_max_delay_seconds,
        backoff_factor=settings.generator.retry_backoff_factor,
    )

    return GeneratorService(
        settings=settings,
        batch_generator=batch_generator,
        repository=repository,
        retry=retry,
        stop_event=stop_event,
    )