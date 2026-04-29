# Deploy readiness (2026-04-28)

## Короткий ответ

**Можно деплоить в staging.**  
**В production — только после smoke-проверки бота в Telegram.**

## Почему

- Автотесты проходят: `pytest -q`.
- Критичный импортный блокер тестов (`ModuleNotFoundError: bot`) снят через `tests/conftest.py`.
- Но продуктовая часть всё ещё содержит смешанную архитектуру (SKILLER + legacy), поэтому лучше идти через staged rollout.

## Минимальный pre-prod чек (обязательно)

1. Проверить `/start` → onboarding → analysis → action loop → evening.
2. Проверить день 3: offer и выбор `€20 / €40 / Подумаю`.
3. Проверить переход в free mode после `Подумаю`.
4. Проверить `/stats` с ADMIN_IDS.
5. Проверить, что background sync в Sheets не влияет на latency ответов.

## Рекомендация по релизу

- rollout: 10% → 50% → 100%
- мониторинг: errors в логах, доля `action_failed`, `crisis_clicked`, и delivery-rate событий в `events`.
