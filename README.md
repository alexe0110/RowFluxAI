# RowFluxAI

Асинхронный пайплайн для row-wise трансформации данных через LLM API.

## 🎯 Что это

Берёт записи из БД → отправляет в LLM с промптом → записывает результат обратно.

**Возможности:**
- Асинхронная обработка (asyncio + asyncpg)
- Провайдеры: OpenAI, Anthropic, YandexGPT
- Автоматические ретраи с exponential backoff
- Валидация SQL и ответов LLM
- Progress bar + graceful shutdown (Ctrl+C)

## 📐 Архитектура

```
[PostgreSQL] ── SELECT ──> [Record] ── LLM ──> [Transformed] ── UPDATE ──> [PostgreSQL]
      │                       │                      │                          │
      └────── Source ─────────┴───── Provider ───────┴──────── Sink ────────────┘
```

```
llm_pipeline/
├── sources/      # Чтение из БД
├── sinks/        # Запись в БД
├── providers/    # OpenAI, Anthropic, Yandex
├── strategies/   # Стратегии обработки
├── validation/   # Валидаторы
└── pipeline.py   # Оркестратор
```

## 🚀 Quick Start

**Вход:**
- PostgreSQL с данными
- API ключ провайдера
- Промпт-файл с инструкциями для LLM

**Выход:**
- Обновлённые записи в БД
- Логи: `pipeline.log`
- Summary в консоли (успех/ошибки/токены/стоимость)

```python
import asyncio
from llm_pipeline import Pipeline, PostgresSource, PostgresSink, AnthropicProvider

async def main():
    pipeline = Pipeline(
        source=PostgresSource(
            query="SELECT id, content FROM articles WHERE status = 'pending'",
            primary_key="id",
            content_field="content"
        ),
        sink=PostgresSink(
            query="UPDATE articles SET content = :content WHERE id = :id"
        ),
        provider=AnthropicProvider(
            model="claude-sonnet-4-20250514",
            temperature=0.7
        ),
        prompt_file="prompts/transform.txt"
    )

    await pipeline.run()

asyncio.run(main())
```

## 🛠 Установка

```bash
# Зависимости
uv sync

# Конфиг — создать .env (см. .env.example)
DB_HOST=localhost
DB_NAME=mydb
ANTHROPIC_API_KEY=sk-ant-...

# Запуск
uv run python -m llm_pipeline
```
