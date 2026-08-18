import axios from 'axios'

export interface ApiErrorDetails {
  message: string
  retryable: boolean
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly code: string | null,
    readonly status: number | null,
    readonly retryable: boolean,
  ) {
    super(message)
    this.name = 'ApiRequestError'
  }
}

export function getApiErrorDetails(
  error: unknown,
  fallbackMessage: string,
): ApiErrorDetails {
  if (error instanceof ApiRequestError) {
    return { message: error.message, retryable: error.retryable }
  }
  if (axios.isAxiosError(error)) {
    return {
      message: error.message || fallbackMessage,
      retryable: !error.response || (error.response.status ?? 0) >= 500,
    }
  }
  return {
    message:
      error instanceof Error && error.message ? error.message : fallbackMessage,
    retryable: true,
  }
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 10_000,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const payload = error.response?.data as
        { error?: { code?: string; message?: string } } | undefined
      const status = error.response?.status ?? null
      const code = payload?.error?.code ?? error.code ?? null
      if (error.code === 'ECONNABORTED') {
        return Promise.reject(
          new ApiRequestError(
            'AI processing took longer than expected. Please retry.',
            code,
            status,
            true,
          ),
        )
      }
      if (payload?.error?.message) {
        return Promise.reject(
          new ApiRequestError(
            payload.error.message,
            code,
            status,
            status === 429 || (status !== null && status >= 500),
          ),
        )
      }
    }
    return Promise.reject(error)
  },
)
