import axios from 'axios'
import { useAuthStore } from '../store/authStore'

// VITE_API_URL is the host root (e.g. "http://localhost:8005"). The "/api/v1"
// versioning prefix is appended here so .env stays the host-only knob.
// If VITE_API_URL is unset we fall back to a relative "/api/v1", which goes
// through the Vite dev-server proxy defined in vite.config.ts.
const API_VERSION_PATH = '/api/v1'
const apiHost = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
const BASE_URL = apiHost ? `${apiHost}${API_VERSION_PATH}` : API_VERSION_PATH

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken) {
        try {
          const res = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
          const { access_token, refresh_token } = res.data
          useAuthStore.getState().setTokens(access_token, refresh_token)
          original.headers.Authorization = `Bearer ${access_token}`
          return apiClient(original)
        } catch {
          useAuthStore.getState().logout()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)
