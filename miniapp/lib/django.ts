import { User } from "@/app/types/user"
import axios, { AxiosInstance } from "axios"

type TokenPair = {
  access: string
  refresh: string
}

class DjangoAPI {
  private api: AxiosInstance
  private plainApi: AxiosInstance
  private username: string
  private password: string

  private accessToken: string | null = null
  private refreshToken: string | null = null
  private isRefreshing = false

  // Очередь для запросов, которые ждут обновления токена
  private failedQueue: any[] = []

  constructor() {
    this.username = process.env.DJANGO_SUPERUSER_USERNAME || ""
    this.password = process.env.DJANGO_SUPERUSER_PASSWORD || ""

    // 1. Создаем экземпляр Axios с базовыми настройками
    this.api = axios.create({
      baseURL: process.env.DJANGO_API_URL || "http://localhost:8000",
      headers: {
        "Content-Type": "application/json",
      },
      validateStatus: (status) => status >= 200 && status < 300,
    })

    this.plainApi = axios.create({
      baseURL: this.api.defaults.baseURL,
      headers: {
        "Content-Type": "application/json",
      },
    })

    // 2. Интерцептор ЗАПРОСА: подкладывает токен перед отправкой
    this.api.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`
        }
        return config
      },
      (error) => Promise.reject(error),
    )

    // 3. Интерцептор ОТВЕТА: ловит 401 ошибку и обновляет токен
    this.api.interceptors.response.use(
      (response) => response, // Если всё ок, просто возвращаем данные
      async (error) => {
        const originalRequest = error.config

        // Если ошибка 401 и это не повторный запрос
        if (error.response?.status === 401 && !originalRequest._retry) {
          // Если мы уже в процессе обновления — ставим запрос в очередь
          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject })
            })
              .then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`
                return this.api(originalRequest)
              })
              .catch((err) => Promise.reject(err))
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            // Пытаемся обновить токен
            const newAccessToken = await this.refreshAccessToken()
            this.processQueue(null, newAccessToken)

            // Повторяем изначальный запрос с новым токеном
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
            return this.api(originalRequest)
          } catch (refreshError) {
            this.processQueue(refreshError, null)
            return Promise.reject(refreshError)
          } finally {
            this.isRefreshing = false
          }
        }

        return Promise.reject(error)
      },
    )
  }

  /**
   * Вспомогательный метод для обработки очереди ожидания
   */
  private processQueue(error: any, token: string | null = null) {
    this.failedQueue.forEach((prom) => {
      if (error) prom.reject(error)
      else prom.resolve(token)
    })
    this.failedQueue = []
  }

  /**
   * Логика получения первой пары токенов
   */
  private async login() {
    const res = await this.api.post<TokenPair>("/api/token/", {
      username: this.username,
      password: this.password,
    })
    this.accessToken = res.data.access
    this.refreshToken = res.data.refresh
    return res.data.access
  }

  /**
   * Обновление accessToken через refreshToken
   */
  private async refreshAccessToken(): Promise<string> {
    try {
      if (!this.refreshToken) return this.login()

      const res = await this.plainApi.post("/api/token/refresh/", {
        refresh: this.refreshToken,
      })

      this.accessToken = res.data.access
      return res.data.access
    } catch (e) {
      // Если refresh тоже протух — полный перелогин
      return this.login()
    }
  }
  async ensureAuth() {
    if (this.accessToken) return

    await this.login()
  }

  // --- Публичные методы API ---

  async getUsersByTelegramId(telegramId: number): Promise<User[]> {
    const res = await this.api.get(`/api/users/`, {
      params: { telegram_id: telegramId },
    })
    return res.data
  }

  async getUserBySubToken(token: string): Promise<User[]> {
    const res = await this.api.get(`/api/users/`, {
      params: { sub_token: token },
    })
    return res.data
  }

  async getUsersByInvitedBy(invitedBy: number) {
    const res = await this.api.get(`/api/users/`, {
      params: { invited_by: invitedBy },
    })
    return res.data
  }

  async createPayment(params: {
    telegram_id: number
    amount: number
    type: string
    months: number
    unique_payload: string
  }) {
    const res = await this.api.post(`/api/payments/create/`, params)
    return res.data
  }

  async getPaymentStatus(paymentId: number) {
    // Ищем по id платеж
    const res = await this.api.get(`/api/payments/`, {
      params: { id: paymentId },
    })

    if (Array.isArray(res.data) && res.data.length > 0) {
      return res.data[0]
    }
    return null
  }

  async getCredentialConfigByTg(telegram_id: string) {
    await this.ensureAuth()

    const res = await this.api.get(`/api/credentials/config-by-tg/`, {
      params: { telegram_id },
    })

    return res.data
  }

  async getFullTrafficStats(telegramId: number) {
    await this.ensureAuth() // Если эндпоинт требует IsAuthenticated
    const res = await this.api.get(`/api/users/full-stats/`, {
      params: { telegram_id: telegramId },
    })
    return res.data
  }

  async unbindCard(telegramId: number) {
    await this.ensureAuth()
    const res = await this.api.post(`/api/payments/unbind-card/`, {
      telegram_id: telegramId,
    })
    return res.data
  }
}

const djangoApi = new DjangoAPI()

export default djangoApi
