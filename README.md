# RowFluxAI
Row-wise data transformation pipeline with LLM


Асинхронный пайплайн для обработки данных из БД через LLM API с автоматической валидацией, retry логикой и детальным логированием.

Флоу:
```
[Database] --SELECT--> [Record] --LLM--> [Transformed] --UPDATE--> [Database]
```