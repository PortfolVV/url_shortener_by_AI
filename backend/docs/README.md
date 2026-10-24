# Backend — документация

FastAPI-приложение с асинхронным SQLAlchemy 2.0 (asyncpg), Redis и Alembic.
Запускается Gunicorn с воркерами `uvicorn.workers.UvicornWorker`.

## 1. Слои и ответственность

| Слой | Где | Ответственность |
| --- | --- | --- |
| API | `src/api/v1/*` | HTTP-контракты, зависимости, коды `fastapi.status`, rate limiting |
| Service | `src/service/*` | Бизнес-правила: выбор хранилища, TTL, дедупликация, агрегация статистики |
| Repository | `src/repository/*` | SQL-запросы через SQLAlchemy, без HTTP-логики |
| Database | `src/database/*` | Engine/session PostgreSQL, клиент Redis, низкоуровневые CRUD-хелперы |
| Models | `src/models/*` | Таблицы `users`, `links`, `clicks` |
| Schemas | `src/schemas/*` | Валидация входа и сериализация выхода (Pydantic v2) |
| Utils | `src/utils/*` | Короткие коды, QR, JWT/bcrypt, валидация URL, limiter |

Правило зависимостей: `api → service → repository → database`. Утилиты
используются сервисами и API.

## 2. Два хранилища

### Redis (анонимные ссылки)

```
shortener:link:<code>          JSON {url, created_at, expires_at}   TTL
shortener:url:<sha256(url)>    <code>                               TTL
```

* Оба ключа получают одинаковый TTL (`ANONYMOUS_LINK_TTL_SECONDS`, 7 дней).
* Дедупликация: индекс URL резервируется через `SET NX` *до* записи ссылки.
  Если индекс уже существует — возвращается найденный код с `reused: true`
  (бизнес-правило #2). Гонки обрабатываются повторными попытками.
* Redis DB 2 используется slowapi-хранилищем (счётчики лимитов).

### PostgreSQL (авторизованные пользователи)

```sql
users  (id uuid pk, email unique, hashed_password, created_at)
links  (id uuid pk, short_code unique, original_url, owner_id -> users,
        expires_at nullable, is_active, created_at)
clicks (id bigserial pk, link_id -> links, clicked_at, referer,
        referer_source, user_agent, ip_address)
```

* `clicks` каскадно удаляются вместе со ссылкой.
* `owner_id` обязателен: таблица `links` в принципе не хранит анонимные ссылки.
* Индексы: `ix_links_short_code` (unique), `ix_links_owner_id_created_at`,
  `ix_clicks_link_id`, `ix_clicks_clicked_at`.

## 3. Потоки запросов

### Создание ссылки

```
POST /api/v1/links
  └─ rate limit (slowapi; ключ = bearer-токен или IP)
  └─ validate_and_normalize_url()
       ├─ синтаксис / схема / порт / креденшалы / публичный суффикс
       ├─ DNS-резолвинг (обязательно)
       └─ HTTP HEAD (best-effort)
  ├─ user is None → RedisLinkStore.save_if_absent()  → ответ reused/new
  └─ user → LinkRepository.create() → commit → QR → ответ
```

### Редирект

```
GET /l/<code>
  └─ Redis GET shortener:link:<code>  → url (is_persistent=false)
  └─ иначе PostgreSQL по short_code
       ├─ нет / is_active=false / истёк → 404 / 410
       └─ url (is_persistent=true)
  └─ 307 RedirectResponse
  └─ BackgroundTask: record_click() с собственной сессией
```

Клик пишется *после* ответа, поэтому недоступность БД не ломает редирект
(ошибка логируется). Referer приводится к хосту в `referer_source`;
отсутствие заголовка → `direct`.

## 4. Эндпоинты

| Метод | Путь | Auth | Успех | Ошибки |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | — | 201 UserOut | 409, 422, 429 |
| POST | `/auth/login` | — | 200 TokenResponse | 401, 422, 429 |
| GET | `/auth/me` | Bearer | 200 UserOut | 401 |
| POST | `/links` | опц. Bearer | 201 LinkResponse | 400, 429, 503 |
| GET | `/links` | Bearer | 200 LinkListResponse | 401 |
| DELETE | `/links/{code}` | Bearer | 204 | 401, 403, 404 |
| GET | `/links/{code}/qr` | — | 200 image/svg+xml | — |
| GET | `/stats/{code}` | Bearer | 200 LinkStatsResponse | 401, 403, 404 |
| GET | `/l/{code}` | — | 307 | 404, 410 |
| GET | `/health` | — | 200 `{status, instance}` | 503 |

OpenAPI: `/api/docs`, `/api/openapi.json`.

### Формат ответа создания

```json
{
  "short_code": "aB3xK9q",
  "short_url": "http://localhost:8080/l/aB3xK9q",
  "original_url": "https://example.com/",
  "created_at": "2026-10-23T10:00:00+00:00",
  "expires_at": "2026-10-30T10:00:00+00:00",
  "qr_code": "data:image/svg+xml;base64,...",
  "is_authenticated": false,
  "reused": false,
  "clicks_count": null
}
```

`qr_code` возвращается только при создании (тяжёлая операция); для списков
используйте `GET /links/{code}/qr`.

## 5. Валидация URL (правило #4)

`src/utils/url_validator.py`:

1. Нормализация: добавление `http://` к `example.com`, lower-case хоста,
   путь `/` по умолчанию.
2. Отклоняются: пустота, пробелы, `ftp://`, креденшалы в URL, битый порт,
   underscore в хосте, неизвестный публичный суффикс, private/loopback/
   link-local/резервные IP.
3. DNS: `getaddrinfo` с таймаутом; ошибка → `400` «домен не существует».
4. HTTP HEAD (если `URL_HTTP_CHECK_ENABLED=true`): `ConnectError`/таймаут
   соединения → `400`; 403/405/TLS-ошибки игнорируются. Редиректы не
   отслеживаются, а `trust_env=False` отключает системные прокси — это
   исключает SSRF через 302 на внутренний адрес.

Именно поэтому `http://asfasf` и `www.somedomain.ashgiasoghgiaso`
отклоняются: у них нет валидного публичного суффикса и/или DNS-записи.

## 6. Безопасность

* Пароли — bcrypt (12 раундов), сравнение в `asyncio.to_thread`, чтобы не
  блокировать event loop; для несуществующего пользователя выполняется
  фиктивное сравнение (timing protection).
* JWT (HS256, PyJWT), `sub` = UUID пользователя, `type=access`.
* SSRF-защита при валидации URL.
* Rate limiting: `10/minute` на создание ссылки (ключ — токен или IP),
  `5/minute` регистрация, `10/minute` логин.
* Nginx добавляет собственный `limit_req` и пробрасывает реальный IP через
  `X-Forwarded-For`. Бэкенд берёт первый адрес из этого заголовка
  (`utils/request.py`) — и для аналитики, и для ключа rate limiter, поэтому
  посетители не делят один bucket Nginx-прокси.
* Короткие коды — `secrets.choice` по алфавиту без похожих символов,
  длина 7 (≈ 3.5×10¹³ комбинаций), проверка коллизий в Redis и PostgreSQL.

## 7. Конфигурация

Настройки читаются в `src/config.py` (pydantic-settings). Полный список —
в `.env.example` корня проекта. Основные:

| Переменная | Default |
| --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://shortener:shortener@localhost:5432/shortener` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | `change-me-in-production` |
| `ANONYMOUS_LINK_TTL_SECONDS` | `604800` |
| `SHORT_CODE_LENGTH` | `7` |
| `URL_HTTP_CHECK_ENABLED` | `true` |
| `ALLOW_PRIVATE_HOSTS` | `false` |
| `LINK_CREATION_RATE_LIMIT` | `10/minute` |

## 8. Alembic

* `alembic/env.py` собирает URL из `settings.database_url` и использует
  `async_engine_from_config`.
* Модели импортируются через `src.models`, поэтому `Base.metadata` всегда
  полон.
* Ревизия `0001_initial` создаёт все таблицы и индексы.

```bash
alembic upgrade head
alembic revision --autogenerate -m "change"
alembic downgrade -1
```

## 9. Тесты

```bash
pip install -r requirements-dev.txt
pytest
```

`tests/test_utils.py` не требует инфраструктуры: проверяются коды, хэши,
JWT, QR и все ветки синтаксической валидации URL.

## 10. Запуск

```bash
# из backend/
gunicorn src.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 2 -b 0.0.0.0:8000 \
  --forwarded-allow-ips '*'
```

Docker-образ: `backend/Dockerfile` (python:3.12-slim, non-root пользователь,
healthcheck через `curl /api/v1/health`).
