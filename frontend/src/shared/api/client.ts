import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 10_000,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const message = (error.response?.data as { error?: { message?: string } })
        ?.error?.message
      if (message) return Promise.reject(new Error(message))
    }
    return Promise.reject(error)
  },
)
