# Конструктор курсов (MVP)

Автоматизация проектирования учебных курсов: два ИИ-агента (структура по ФГОС и блочный контент с RAG), веб-редактор блоков и опциональная локальная LLM через **llama.cpp**.

## Что умеет система

1. Преподаватель вводит метаданные курса и загружает PDF (до 100 страниц).
2. Агент №1 строит иерархию разделов (часы, цели обучения) в JSON.
3. Агент №2 генерирует независимые блоки: презентация, теория, самопроверка, тест. Факты берутся из загруженных файлов (RAG).
4. В редакторе блок можно править, перегенерировать, удалить, переместить; сохраняется история версий.

Нормативы: структура ≤ 30 с, блок ≤ 10 с (таймауты LLM задаются в `.env`).

## Требования

- Python 3.11+
- Docker Desktop (рекомендуется) **или** PostgreSQL 16 + Redis 7
- Для облачной LLM: ключ OpenAI
- Для локальной LLM: `llama-server` из [llama.cpp](https://github.com/ggerganov/llama.cpp) и GGUF-модель

## Быстрый старт (Docker)

```bash
cp .env.example .env
# укажите OPENAI_API_KEY либо настройте llama.cpp (см. ниже)

docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser  # опционально
```

| Сервис | URL |
| --- | --- |
| Редактор | http://localhost:8000/ |
| API | http://localhost:8000/api/ |
| Админка | http://localhost:8000/admin/ |
| Flower | http://localhost:5555/ |
| Health | http://localhost:8000/api/health/ |

## Локальный запуск без Docker

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
celery -A core worker --loglevel=info
```

В `.env` задайте `POSTGRES_HOST` / `REDIS_URL` под свою машину.

## Подключение LLM

Провайдер выбирается переменной `LLM_PROVIDER`.

### 1. OpenAI (по умолчанию)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
LLM_EMBEDDING_MODEL=text-embedding-3-small
```

### 2. llama.cpp server (рекомендуемый локальный режим)

Сервер llama.cpp совместим с OpenAI API (`/v1/chat/completions`, при поддержке модели — `/v1/embeddings`).

Соберите [llama.cpp](https://github.com/ggerganov/llama.cpp) и запустите:

```PowerShell
llama-server.exe -m model.gguf -ngl 99 -c 16384 --host 0.0.0.0 --port 11434 --embeddings --pooling mean
```

В `.env`:

```env
LLM_PROVIDER=llamacpp
LLM_BASE_URL=http://127.0.0.1:8080/v1 
или 
LLM_BASE_URL=http://host.docker.internal:11434/v1/ если модель запущена вне Docker на локальной машине
LLM_API_KEY=sk-local
LLM_MODEL=local-model
LLM_EMBEDDING_MODEL=local-model
LLM_STRUCTURE_TIMEOUT=30
LLM_BLOCK_TIMEOUT=10
```

Через Compose (GGUF должен лежать в `./models/model.gguf` или имя задаётся `LLAMA_CPP_MODEL_FILE`):
Раскомментировать строки в docker-compose.yml

```bash
docker compose --profile local-llm up -d
```

Для контейнеров backend/celery укажите `LLM_BASE_URL=http://llamacpp:8080/v1`.

Если у сервера нет эмбеддингов, RAG автоматически переключается на лексический поиск по чанкам PDF — генерация блоков всё равно опирается на ваши материалы.

### 3. llama-cpp-python (GGUF в процессе Python)

Нужен пакет, который **не** входит в основной `requirements.txt` (сборка зависит от CPU/GPU):

```bash
pip install llama-cpp-python
```

```env
LLM_PROVIDER=llamacpp_python
LLAMA_CPP_MODEL_PATH=./models/model.gguf
LLAMA_CPP_N_CTX=8192
LLAMA_CPP_N_GPU_LAYERS=0
LLAMA_CPP_CHAT_FORMAT=chatml
```

Для CUDA/Metal смотрите инструкцию установки `llama-cpp-python`. Этот режим удобен для отладки; для нагрузки используйте отдельный `llama-server`.

Текущий провайдер: `GET /api/llm/`.

## API (кратко)

Аутентификация MVP: заголовок `X-Instructor-Id` должен совпадать с `instructor_id` курса при изменениях.

| Метод | Путь | Назначение |
| --- | --- | --- |
| POST | `/api/courses/` | Создать курс |
| POST | `/api/courses/{id}/generate-structure/` | Агент №1 |
| POST | `/api/courses/{id}/generate-all-blocks/` | Агент №2 по всем разделам |
| GET | `/api/courses/{id}/preview/` | Полный снимок курса |
| POST | `/api/materials/` | PDF (`multipart`: `course`, `filepath`) |
| POST | `/api/sections/{id}/generate-blocks/` | Блоки одного раздела |
| PATCH | `/api/blocks/{id}/` | Ручная правка |
| POST | `/api/blocks/{id}/regenerate/` | Перегенерация (`instruction`) |
| GET | `/api/blocks/{id}/history/` | История версий |
| POST | `/api/blocks/reorder/` | `[{"id","order"}]` |
| POST | `/api/blocks/bulk-delete/` | `{"ids":[...]}` |

Пример создания курса:

```bash
curl -X POST http://localhost:8000/api/courses/ \
  -H "Content-Type: application/json" \
  -d '{
    "instructor_id": "instructor-1",
    "instructor_fio": "Иванов И.И.",
    "discipline_name": "Информатика",
    "education_direction": "09.03.01 Информатика и вычислительная техника",
    "course_hours": 36
  }'
```

## Архитектура

```
apps/common          DTO, протоколы, разбор JSON от LLM
apps/ai_agents       Агенты, промпты, адаптеры OpenAI / llama.cpp, RAG
apps/courses         Курс, разделы, блоки, история
apps/uploads         PDF → чанки (+ эмбеддинги при наличии)
apps/editor          Веб-редактор блоков
```

Клиент LLM выбирается фабрикой `build_ai_client` (`apps/ai_agents/adapters/factory.py`). Генераторы работают с Pydantic-DTO и не зависят от Django-моделей — их проще тестировать.

## Тесты и типы

```bash
pip install -r requirements-dev.txt
pytest
pytest --cov
mypy apps core
```

Pytest использует SQLite (`core.settings_test`), LLM и Celery не нужны.

## Модель данных

- `courses` — метаданные и статус (`draft` / `generating` / `ready` / `error`)
- `course_sections` — разделы, часы, цели (JSON)
- `content_blocks` — UUID, тип, `content`, `source_meta`, версия
- `block_revisions` — история правок
- `user_materials` / `material_embeddings` — PDF и чанки для RAG

## Ограничения MVP

- Формат материалов: только PDF, не более 100 страниц.
- Нагрузка «50 одновременных генераций» требует пула Celery-воркеров и внешнего LLM-сервера; один процесс `llamacpp_python` для этого не рассчитан.
- Таймауты для локальной модели нужно подбирать вручную в файлах .env и apps/ai_agents/tasks.py в зависимости от железа.
- Полноценная учётная запись преподавателя не реализована (заголовок `X-Instructor-Id`).
