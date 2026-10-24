import axios from 'axios'

export const TOKEN_STORAGE_KEY = 'shortly_token'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 25000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (error.response?.status === 401 && token && !error.config?.url?.includes('/auth/login')) {
      window.dispatchEvent(new CustomEvent('auth:expired'))
    }
    return Promise.reject(error)
  },
)

export function getApiErrorMessage(error) {
  if (!error?.response) {
    if (error?.code === 'ECONNABORTED') {
      return 'Сервер не ответил вовремя. Попробуйте ещё раз.'
    }
    return 'Не удалось связаться с сервером. Проверьте подключение.'
  }

  const { status, data } = error.response
  const detail = data?.detail

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg || 'Некорректные данные')
      .join('; ')
  }
  if (typeof detail === 'string') {
    return detail
  }

  const fallbacks = {
    400: 'Некорректный запрос. Проверьте ссылку.',
    401: 'Требуется авторизация.',
    403: 'Недостаточно прав для этого действия.',
    404: 'Ничего не найдено.',
    409: 'Такая запись уже существует.',
    410: 'Ссылка больше не активна.',
    422: 'Проверьте правильность заполнения полей.',
    429: 'Слишком много запросов. Попробуйте чуть позже.',
    500: 'Внутренняя ошибка сервера. Попробуйте позже.',
    503: 'Сервис временно недоступен. Попробуйте позже.',
  }
  return fallbacks[status] || 'Что-то пошло не так. Попробуйте ещё раз.'
}

export default api
