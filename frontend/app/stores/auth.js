import { defineStore } from 'pinia'

import api, { TOKEN_STORAGE_KEY } from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_STORAGE_KEY) || '',
    user: null,
    loading: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },

  actions: {
    setToken(token) {
      this.token = token || ''
      if (token) {
        localStorage.setItem(TOKEN_STORAGE_KEY, token)
      } else {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
      }
    },

    async login(credentials) {
      this.loading = true
      try {
        const { data } = await api.post('/auth/login', credentials)
        this.setToken(data.access_token)
        this.user = data.user
        return data.user
      } finally {
        this.loading = false
      }
    },

    async register(payload) {
      this.loading = true
      try {
        await api.post('/auth/register', payload)
        return await this.login({
          email: payload.email,
          password: payload.password,
        })
      } finally {
        this.loading = false
      }
    },

    async fetchMe() {
      if (!this.token) return null
      const { data } = await api.get('/auth/me')
      this.user = data
      return data
    },

    logout() {
      this.setToken('')
      this.user = null
    },
  },
})
