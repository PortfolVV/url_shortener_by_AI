# Shortly — URL Shortener

Полнофункциональный сократитель ссылок: **FastAPI + PostgreSQL + Redis** на
бэкенде, **Vue 3 + Vite** на фронтенде, **Nginx** в роли reverse proxy,
load balancer и сервера статики. Всё упаковано в Docker Compose.

Интерфейс выполнен в стиле **Glassmorphism** (полупрозрачные панели,
`backdrop-filter: blur`, тонкие границы, мягкие тени, анимированные
градиентные сферы).

---

## 1. Быстрый старт

```bash
cd url_shortener_project
cp .env.example .env          # при необходимости поменяйте JWT_SECRET_KEY
docker compose up --build -d
```

| Что | Адрес |
| --- | --- |
| Приложение | <http://localhost:8080> |
| Swagger UI | <http://localhost:8080/api/docs> |
| ReDoc | <http://localhost:8080/api/redoc> |
| Health check | <http://localhost:8080/api/v1/health> |

> **Почему на :8080 стоит отдельный прокси.** На машине разработки loopback
> имеет MTU 65536, и ядро теряет крупные TCP-сегменты: любой ответ больше
> ~12 КиБ (включая JS-бандл Vite) зависает, хотя сервер пишет `200`.
> Поэтому перед Nginx добавлен крошечный TCP/MSS-прокси (MSS 1200), а
> контейнерная сеть переведена на MTU 1500. Nginx по-прежнему отдаёт SPA и
> балансирует API. Подробный разбор и как убрать workaround на здоровом
> хосте — в [разделе 10](#10-диагностика-почему-ui-зависал-и-зачем-нужен-proxy).

Проверить, что живы все контейнеры:

```bash
docker compose ps
docker compose logs -f nginx
```

Миграции Alembic применяются автоматически одноразовым сервисом `migrate`
до старта бэкендов (`depends_on: service_completed_successfully`).

Остановить / удалить данные:

```bash
docker compose down            # остановить
docker compose down -v         # остановить и удалить volume-ы (БД, Redis)
```

---

## 2. Архитектура

```text
                        ┌──────────────────────────────────────────┐
   browser :8080 ──────▶│ TCP/MSS proxy (host net, MSS 1200)       │
                        │ TCP forwarder + PROXY v1 (real client IP)│
                        └───────────────────┬──────────────────────┘
                                            │ 127.0.0.1:8081
                        ┌───────────────────▼──────────────────────┐
                        │  Nginx (LB + static + edge rate limit)   │
                        │  /            → Vue SPA (shared volume)  │
                        │  /api/        → upstream (least_conn)    │
                        │  /l/<code>    → upstream                 │
                        └───────────────┬──────────────────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
             ┌───────────────┐                     ┌───────────────┐
             │  backend_1    │                     │  backend_2    │
             │ gunicorn ×2   │                     │ gunicorn ×2   │
             │ FastAPI       │                     │ FastAPI       │
             └───┬───────┬───┘                     └───┬───────┬───┘
                 │       │                             │       │
                 │       └──────────────┬──────────────┘       │
                 ▼                      ▼                      ▼
          ┌────────────┐        ┌────────────┐        ┌────────────┐
          │ PostgreSQL │        │   Redis    │        │  migrate   │
          │ users      │        │ anon links │        │ alembic    │
          │ links      │        │ dedupe idx │        │ (one-shot) │
          │ clicks     │        │ rate limit │        └────────────┘
          └────────────┘        └────────────┘
```

* **2 реплики бэкенда** × 2 Gunicorn/Uvicorn воркера = 4 процесса,
  Nginx балансирует через `least_conn` + `keepalive`. Имена реплик
  резолвятся динамически (`server ... resolve`, `resolver` из
  `/etc/resolv.conf`), поэтому пересоздание контейнера бэкенда не требует
  перезапуска Nginx.
* **Redis DB 0** — анонимные ссылки, **Redis DB 2** — счётчики rate limiter.
* **PostgreSQL** — пользователи, ссылки авторизованных пользователей,
  клики и аналитика.
* Nginx дополнительно ограничивает создание ссылок (`20 r/m` на IP),
  FastAPI/slowapi — свой лимит (`10/minute` на IP или токен).
* **TCP/MSS-прокси** (`proxy/loopback_proxy.py`) стоит только перед
  браузерным портом. Он ограничивает TCP MSS значением 1200 и передаёт
  PROXY v1, чтобы Nginx и аналитика видели настоящий IP клиента. Это
  workaround для бага крупных TCP-сегментов на loopback (раздел 10).
* **Контейнерная сеть Compose** создаётся с MTU 1500, чтобы ответы
  backend → Nginx тоже не упирались в тот же лимит.

### Слои бэкенда

```
api/v1        HTTP-слой: роутеры, зависимости, коды ответов
service       бизнес-логика: выбор хранилища, TTL, дедупликация, клики
repository    запросы к PostgreSQL (ORM)
database      engine/session PostgreSQL + клиент и CRUD Redis
utils         короткие коды, QR, JWT/bcrypt, валидация URL, rate limit
models        SQLAlchemy-модели
schemas       Pydantic-схемы запросов/ответов
```

---

## 3. Строгие бизнес-правила — как реализованы

| Правило | Реализация |
| --- | --- |
| Ссылки анонимов — **только Redis**, фиксированный TTL | `LinkService._create_anonymous_link` → `RedisLinkStore`; TTL = `ANONYMOUS_LINK_TTL_SECONDS` (7 дней). В PostgreSQL анонимные ссылки не пишутся. |
| Повторное сокращение того же URL возвращает **существующую** ссылку | Атомарный индекс `shortener:url:<sha256(url)>` → code (`SET NX`) в `RedisLinkStore.save_if_absent`; ответ помечается `reused: true`. |
| Все HTTP-ошибки — коды из `fastapi.status` | Во всех роутерах и сервисах используются `status.HTTP_400_BAD_REQUEST`, `HTTP_401_UNAUTHORIZED`, `HTTP_404_NOT_FOUND`, `HTTP_409_CONFLICT`, `HTTP_410_GONE`, `HTTP_429_TOO_MANY_REQUESTS`, `HTTP_503_SERVICE_UNAVAILABLE`. |
| Строгая валидация URL (синтаксис + существование домена) | `utils/url_validator.py`: `http/https`, запрет пробелов/креденшалов, проверка публичного суффикса через `tldextract`, DNS-резолвинг, опциональный HTTP HEAD, блокировка private/loopback/reserved адресов (SSRF). |
| Ссылки и статистика авторизованных — **только PostgreSQL** | `Link`/`Click` модели; клики пишутся фоновой задачей `record_click` с отдельной сессией. |
| Glassmorphism | `frontend/app/assets/styles/glass.css` + компоненты Atomic Design. |
| QR-код | `utils/qr.py`, SVG → `data:image/svg+xml;base64,...` в ответе создания, отдельный эндпоинт `GET /api/v1/links/{code}/qr`. |
| Rate limiting | slowapi + Redis (глобально между воркерами) и `limit_req` в Nginx. |
| Load balancing | Nginx `upstream` c `backend_1`/`backend_2`, `least_conn`, health checks, Gunicorn с 2 воркерами. |

---

## 4. Структура проекта

```text
url_shortener_project/
├── docker-compose.yml
├── nginx/
│   ├── docker-entrypoint-wrapper.sh   # автодетект DNS (Docker / Podman)
│   └── templates/nginx.conf.template  # envsubst → /etc/nginx/nginx.conf
├── proxy/
│   └── loopback_proxy.py              # MSS/PROXY workaround (см. раздел 10)
├── backend/
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/0001_initial.py
│   ├── docs/README.md
│   ├── src/
│   │   ├── api/v1/          # auth.py, links.py, stats.py, health.py
│   │   ├── database/
│   │   │   ├── postgre/     # base_class.py, session.py, crud.py
│   │   │   └── redis/       # client.py, crud.py
│   │   ├── models/          # user.py, link.py, click.py
│   │   ├── repository/      # user/link/click repositories
│   │   ├── schemas/         # auth.py, link.py, stats.py
│   │   ├── service/         # auth/link/stats services
│   │   ├── utils/           # hashing, qr, security, url_validator, rate_limit
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
└── frontend/
    ├── app/
    │   ├── atoms/           # BaseButton, BaseInput, GlassCard, ...
    │   ├── molecules/       # UrlForm, LinkResult, AuthForm, LinkItem, StatCard
    │   ├── organisms/       # HeaderBar, ShortenerPanel, AuthPanel, LinksList, AnalyticsPanel
    │   ├── templates/       # DefaultTemplate, AuthTemplate, DashboardTemplate
    │   ├── pages/           # Home, Login, Register, Dashboard, Stats, NotFound
    │   ├── router/
    │   ├── services/        # axios API client
    │   ├── stores/          # Pinia auth store
    │   ├── utils/
    │   └── assets/styles/glass.css
    ├── docs/README.md
    ├── index.html
    ├── vite.config.js
    └── Dockerfile
```

---

## 5. API

Базовый префикс — `/api/v1`.

| Метод | Путь | Auth | Назначение |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | — | Регистрация |
| `POST` | `/auth/login` | — | JWT-токен |
| `GET` | `/auth/me` | Bearer | Текущий пользователь |
| `POST` | `/links` | опционально | Создать ссылку (Redis или PostgreSQL) |
| `GET` | `/links` | Bearer | Список ссылок с числом кликов |
| `DELETE` | `/links/{code}` | Bearer | Удалить свою ссылку |
| `GET` | `/links/{code}/qr` | — | SVG QR-код |
| `GET` | `/stats/{code}` | Bearer | Клики, время, referer |
| `GET` | `/l/{code}` | — | Редирект (307) + запись клика |
| `GET` | `/health` | — | Проверка PostgreSQL и Redis |

### Примеры

```bash
# Анонимная ссылка (TTL фиксирован, повторный вызов вернёт тот же код)
curl -s -X POST http://localhost:8080/api/v1/links \
  -H 'Content-Type: application/json' \
  -d '{"original_url":"https://example.com"}'

# Регистрация и логин
curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"supersecret1"}'

TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"supersecret1"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

# Ссылка с TTL 1 день (null = бессрочная)
curl -s -X POST http://localhost:8080/api/v1/links \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"original_url":"https://example.com","ttl_seconds":86400}'

# Редирект и статистика
curl -i http://localhost:8080/l/<code>
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/v1/stats/<code>

# QR в файл
curl -s http://localhost:8080/api/v1/links/<code>/qr -o qr.svg
```

Проверка балансировки:

```bash
for _ in 1 2 3 4 5 6; do
  curl -sI http://localhost:8080/api/v1/health | grep -i x-instance
done
```

---

## 6. Миграции Alembic

Автоматически: сервис `migrate` выполняет `alembic upgrade head` при
`docker compose up`.

Вручную:

```bash
# применить
docker compose run --rm migrate alembic upgrade head

# новая миграция после изменения моделей
docker compose run --rm migrate alembic revision --autogenerate -m "add something"

# откат на одну ревизию
docker compose run --rm migrate alembic downgrade -1
```

Начальная миграция — `backend/alembic/versions/0001_initial.py`
(users, links, clicks + индексы).

---

## 7. Локальная разработка без Docker

### Бэкенд

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

export DATABASE_URL='postgresql+asyncpg://shortener:shortener@localhost:5432/shortener'
export REDIS_URL='redis://localhost:6379/0'
export JWT_SECRET_KEY='local-dev-secret'

alembic upgrade head
uvicorn src.main:app --reload --port 8000
```

Нужны локальные PostgreSQL и Redis (или поднимайте только их:
`docker compose up -d postgres redis`).

### Фронтенд

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, /api и /l проксируются на :8000
```

### Тесты

```bash
cd backend
pytest
```

Покрыты утилиты: генерация кодов, bcrypt/JWT, QR, строгая валидация URL
(включая `http://asfasf`, `www.somedomain.ashgiasoghgiaso`, private IP).

---

## 8. Конфигурация

Все параметры задаются переменными окружения (см. `.env.example`).
Ключевые:

| Переменная | По умолчанию | Описание |
| --- | --- | --- |
| `BASE_URL` | `http://localhost:8080` | База для коротких ссылок |
| `APP_PORT` | `8080` | Браузерный порт (слушает TCP/MSS-прокси) |
| `NGINX_INTERNAL_PORT` | `8081` | Внутренний порт Nginx (только loopback) |
| `PROXY_MSS` | `1200` | MSS workaround-прокси (для бага loopback) |
| `JWT_SECRET_KEY` | `change-me-in-production` | **Обязательно заменить** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Время жизни JWT |
| `ANONYMOUS_LINK_TTL_SECONDS` | `604800` | TTL анонимных ссылок |
| `URL_HTTP_CHECK_ENABLED` | `true` | Доп. HTTP HEAD-проверка |
| `ALLOW_PRIVATE_HOSTS` | `false` | Разрешать private IP (только локально!) |
| `LINK_CREATION_RATE_LIMIT` | `10/minute` | slowapi-лимит создания |
| `RATE_LIMIT_ENABLED` | `true` | Глобальный выключатель лимитера |

---

## 9. Что важно знать

* Короткие ссылки отдаются по пути **`/l/<code>`**, а не `/<code>` — это
  исключает конфликт с маршрутами SPA (`/login`, `/dashboard`, ...).
* DNS-проверка домена обязательна. HTTP HEAD — best-effort: сайты, которые
  блокируют HEAD (403/405), не отбрасываются; а вот недоступный TCP-порт
  (`ConnectError`) считается ошибкой. В закрытых сетях проверку можно
  выключить через `URL_HTTP_CHECK_ENABLED=false`.
* Анонимные ссылки не имеют аналитики по определению (их нет в PostgreSQL).
* Клик записывается фоновой задачей после отправки редиректа, поэтому
  задержка редиректа не зависит от записи в БД.
* Для продакшена: замените `JWT_SECRET_KEY`, пароли PostgreSQL, включите TLS
  на Nginx и не выставляйте `ALLOW_PRIVATE_HOSTS=true`.

---

## 10. Диагностика: почему UI зависал и зачем нужен proxy

### Симптом

Браузер открывал `http://localhost:8080`, получал HTML (683 байта) и CSS
(10 460 байт), но страница оставалась пустой: `<div id="app"></div>` так и не
заполнялся. В Network уходил в бесконечность запрос
`/assets/index-*.js` (167 202 байта). Nginx при этом писал в access log
`200 167202`, то есть считал, что отдал файл целиком.

### Что показала диагностика

* `curl` того же JS-файла обрывался примерно после 12 КиБ и висел до
  таймаута. Файл в 12 288 байт скачивался, 16 384 байта — уже нет.
* Тот же эффект воспроизводится **без проекта**: обычный
  `python3 -m http.server` и чистый `nginx:alpine` на этом хосте отдают
  небольшой файл, но зависают на 16 КиБ. Внутри контейнера и из соседнего
  контейнера тот же файл скачивается за миллисекунды.
* `ss -tin` на зависшем соединении показывает огромный `mss` (32768),
  `lost`, `cwnd:1` и повторные передачи. Сервер уже отправил данные в
  сокет, но клиент их не получает.
* Причина — не Vue, не FastAPI и не Nginx. У loopback на этой машине MTU
  65 536, у контейнерного интерфейса Podman/pasta — 65 520. TCP
  договаривается о сегментах в десятки килобайт, а ядро на этом пути их
  теряет. Всё, что больше ~12 КиБ, зависает. Основной JS-бандл Vite
  (167 КиБ) попадает в эту категорию; CSS и ленивые чанки (<12 КиБ)
  загружались нормально.

### Что изменено

1. **`proxy/loopback_proxy.py`** — прозрачный TCP-форвардер, запущенный в
   сервисе `proxy` с `network_mode: host`. Он слушает браузерный порт 8080
   и передаёт трафик в Nginx на `127.0.0.1:8081`. На слушающем сокете
   выставляется `TCP_MAXSEG=1200` (наследуется accepted-соединениями), а на
   upstream-сокете — до `connect()`, поэтому обе стороны используют
   маленькие сегменты. Дополнительно прокси отправляет PROXY v1, чтобы
   Nginx видел настоящий IP клиента.
2. **Nginx** слушает `80 proxy_protocol` (порт 8081 опубликован только на
   loopback) и внутренний `8080` без PROXY-заголовка — для healthcheck.
   `set_real_ip_from` + `real_ip_header proxy_protocol` возвращают
   `$remote_addr` реальный адрес браузера, поэтому лимиты и аналитика
   работают как раньше.
3. **Сеть Compose** создаётся с MTU 1500 (`networks.default.driver_opts`,
   ключ `com.docker.network.driver.mtu` — его понимают и Docker, и Podman),
   чтобы ответы backend → Nginx не упирались в тот же баг.
4. Healthcheck Nginx ходит на `127.0.0.1:8080`, а не на `localhost`:
   `localhost` может сначала резолвиться в `::1`, а Nginx слушает IPv4.

### Как убрать workaround на здоровом хосте

Прокси безвреден и на нормальной машине, но если он не нужен:

1. В `docker-compose.yml` удалите сервис `proxy`, верните Nginx
   `ports: ["${APP_PORT:-8080}:80"]` и удалите блок
   `networks.default.driver_opts` (MTU 1500 не обязателен).
2. В `nginx/templates/nginx.conf.template` замените
   `listen 80 proxy_protocol;` на `listen 80;`, удалите `listen 8080;`
   (или оставьте, если нужен внутренний healthcheck) и строки
   `set_real_ip_from` / `real_ip_header proxy_protocol`.
3. Верните healthcheck на `http://127.0.0.1/healthz`.
4. Каталог `proxy/` можно удалить.

`network_mode: host` — Linux-специфичный; на Docker Desktop (macOS/Windows)
используйте вариант без прокси.

### Почему нельзя было обойтись правкой фронтенда

Бандл 167 КиБ нельзя разбить на куски <12 КиБ: один только runtime Vue
больше лимита. Gzip уменьшает его до ~73 КиБ — всё ещё выше порога.
`sendfile off`, `tcp_nopush`, буферы Nginx и chunked-ответы не помогают:
данные теряются ниже HTTP, на TCP-пути хоста. Обычный Python-сервер
воспроизводит проблему так же, как Nginx.
