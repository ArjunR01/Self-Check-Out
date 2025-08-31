import axios from 'axios'
import { getTokens } from './auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  const t = getTokens()
  if (t?.token) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${t.token}`
  }
  return config
})

export default api

