// lib/django.ts

type TokenPair = {
  access: string
  refresh: string
}

export class DjangoAPI {
  private base: string
  private username: string
  private password: string

  private accessToken: string | null = null
  private refreshToken: string | null = null
  private isAuthenticating = false

  constructor() {
    this.base = process.env.DJANGO_API_URL || "http://localhost:8000"
    this.username = process.env.DJANGO_SUPERUSER_USERNAME || ""
    this.password = process.env.DJANGO_SUPERUSER_PASSWORD || ""
  }

  // -----------------------------
  // 1. Авторизация (один раз)
  // -----------------------------
  private async loginOnce() {
    if (this.accessToken || this.isAuthenticating) return

    this.isAuthenticating = true

    const res = await fetch(`${this.base}/api/token/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: this.username,
        password: this.password,
      }),
    })

    if (!res.ok) {
      this.isAuthenticating = false
      throw new Error("Ошибка авторизации в Django API")
    }

    const data: TokenPair = await res.json()
    this.accessToken = data.access
    this.refreshToken = data.refresh
    this.isAuthenticating = false
  }

  // -----------------------------
  // 2. Обновление токена
  // -----------------------------
  private async refreshAccessToken() {
    if (!this.refreshToken) return this.loginOnce()

    const res = await fetch(`${this.base}/api/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: this.refreshToken }),
    })

    if (!res.ok) {
      // refresh истёк → логинимся заново
      const errorData = await res.text()
      console.error(`🔴 Django API Error [${res.status}]`)
      console.error(`Детали:`, errorData)
      return this.loginOnce()
    }

    const data = await res.json()
    this.accessToken = data.access
  }

  // -----------------------------
  // 3. Универсальный запрос
  // -----------------------------
  private async request(url: string, options: RequestInit = {}) {
    if (!this.accessToken) {
      await this.loginOnce()
    }

    const res = await fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        Authorization: `Bearer ${this.accessToken}`,
      },
    })

    // Если токен истёк → обновляем и повторяем запрос
    if (res.status === 401) {
      await this.refreshAccessToken()

      const retry = await fetch(url, {
        ...options,
        headers: {
          ...(options.headers || {}),
          Authorization: `Bearer ${this.accessToken}`,
        },
      })

      if (!retry.ok) {
        throw new Error(`Ошибка запроса после refresh: ${retry.status}`)
      }

      return retry.json()
    }

    if (!res.ok) {
      throw new Error(`Ошибка запроса: ${res.status}`)
    }

    return res.json()
  }

  // -----------------------------
  // 4. Твои API методы
  // -----------------------------
  async getUsersByTelegramId(telegramId: number) {
    return this.request(`${this.base}/api/users/?telegram_id=${telegramId}`)
  }

  async getUsersByInvitedBy(invitedBy: number) {
    return this.request(`${this.base}/api/users/?invited_by=${invitedBy}`)
  }

  async createPayment(params: {
    telegram_id: number
    amount: number
    type: string
    months: number
    unique_payload: string
  }) {
    console.log("createPayment" + params)
    return this.request(`${this.base}/api/payments/create/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    })
  }
}
