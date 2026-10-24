# Frontend — документация

Vue 3 (Composition API, `<script setup>`) + Vite + Pinia + Vue Router.
Структура строго по **Atomic Design**, дизайн — **Glassmorphism**.

## 1. Atomic Design

```text
app/
├── atoms/       мельчайшие элементы, без знания о бизнес-логике
│   ├── BaseButton.vue      варианты primary/ghost/danger/link, loading
│   ├── BaseInput.vue       v-model, label, error, hint, useId()
│   ├── GlassCard.vue       стеклянная панель (blur + border + shadow)
│   ├── BaseSpinner.vue
│   └── BaseBadge.vue       tone: info/success/warning/danger/neutral
│
├── molecules/   композиции атомов
│   ├── UrlForm.vue         URL + TTL + клиентская валидация
│   ├── LinkResult.vue      короткая ссылка, копирование, QR
│   ├── AuthForm.vue        email/password + валидация
│   ├── LinkItem.vue        карточка ссылки, действия
│   └── StatCard.vue        метрика аналитики
│
├── organisms/   самостоятельные секции
│   ├── HeaderBar.vue       навигация, состояние авторизации
│   ├── ShortenerPanel.vue  форма + запрос POST /links + результат
│   ├── AuthPanel.vue       login/register + обработка 401/409/429
│   ├── LinksList.vue       сетка ссылок, loading/empty/error
│   └── AnalyticsPanel.vue  метрики, топ referer, таблица кликов
│
├── templates/   каркасы страниц
│   ├── DefaultTemplate.vue     header + page + footer
│   ├── AuthTemplate.vue        split-layout с промо-блоком
│   └── DashboardTemplate.vue   широкий каркас кабинета
│
└── pages/       маршруты
    ├── HomePage.vue
    ├── LoginPage.vue
    ├── RegisterPage.vue
    ├── DashboardPage.vue
    ├── StatsPage.vue
    └── NotFoundPage.vue
```

Вспомогательные каталоги: `router/`, `stores/` (Pinia), `services/` (axios),
`utils/` (форматирование дат, clipboard), `assets/styles/glass.css`.

## 2. Маршруты

| Путь | Компонент | Доступ |
| --- | --- | --- |
| `/` | HomePage | все |
| `/login` | LoginPage | только гость |
| `/register` | RegisterPage | только гость |
| `/dashboard` | DashboardPage | `requiresAuth` |
| `/stats/:code` | StatsPage | `requiresAuth` |
| `*` | NotFoundPage | все |

`router.beforeEach` проверяет наличие токена и при необходимости вызывает
`auth.fetchMe()`; при 401 срабатывает событие `auth:expired`, стор очищается,
пользователь попадает на `/login`.

## 3. Состояние и API

`stores/auth.js` (Pinia):

* `token`, `user`, `loading`;
* `login`, `register`, `fetchMe`, `logout`;
* токен хранится в `localStorage` под ключом `shortly_token`.

`services/api.js`:

* `baseURL = VITE_API_BASE_URL || '/api/v1'` — в production относительный
  путь, Nginx проксирует на бэкенд;
* interceptor добавляет `Authorization: Bearer`;
* `getApiErrorMessage()` переводит `detail` FastAPI и HTTP-статусы
  (400/401/403/404/409/410/422/429/5xx) в понятные русские сообщения.

## 4. Дизайн-система

`assets/styles/glass.css` содержит:

* CSS-переменные (цвета, радиусы, тени, шрифты);
* анимированный фон: три градиентные сферы + зерно;
* `.glass-card` — `backdrop-filter: blur(24px) saturate(150%)`,
  полупрозрачный градиент, внутренние блики, мягкая тень;
* `.btn--*`, `.input`, `.select`, `.badge`, `.alert`, `.data-table`,
  `.empty-state`, `.skeleton`;
* адаптивность, `prefers-reduced-motion`.

Компоненты добавляют только layout-стили в `<style scoped>`.

## 5. Запуск

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173
```

Vite проксирует `/api` и `/l` на `http://localhost:8000`
(переопределяется `VITE_PROXY_TARGET`).

Production-сборка:

```bash
npm run build     # dist/
npm run preview
```

В Docker Compose сервис `frontend_build` собирает бандл и копирует его в
именованный volume `frontend_dist`, который Nginx отдаёт как статику.
SPA-fallback настроен в `nginx/templates/nginx.conf.template`
(`try_files ... /index.html`).

## 6. UX-детали

* Анонимный пользователь видит бейдж «7 дней» и не может выбрать TTL.
* Авторизованный — select с вариантами 1 час / 1 день / 7 дней / 30 дней /
  бессрочно.
* Если ссылка уже существовала (Redis-дедупликация), показывается
  «Уже существовала» и пояснение.
* QR-код — SVG data URI, рендерится как `<img>`; отдельная ссылка открывает
  `/api/v1/links/{code}/qr`.
* Копирование использует Clipboard API с fallback на `execCommand`.
* В кабинете — количество кликов по каждой ссылке, удаление с подтверждением.
* На странице статистики — топ referer-источников и таблица последних
  переходов (время, источник, referer, user-agent, IP).
