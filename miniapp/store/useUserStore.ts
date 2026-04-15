import { User } from "@/app/types/user"
import { api } from "@/lib/api"
import { create } from "zustand"

export interface TrafficData {
  usedGb: string
  totalGb: string
  percent: number
  details?: any[]
}

interface UserStore {
  user: User | null
  traffic: TrafficData | null
  loading: boolean
  error: string | null
  initData: string

  fetchUser: (telegram_id?: number) => Promise<void>
  fetchBySubToken: (token: string) => Promise<void>
  fetchTraffic: () => Promise<void>
  setUser: (u: User | null) => void
  setError: (msg: string | null) => void
  setLoading: (v: boolean) => void
  setInitData: (v: string) => void
}

export const useUserStore = create<UserStore>((set, get) => ({
  user: null,
  traffic: null,
  loading: true,
  error: null,
  initData: "",

  // Метод 1: Загрузка по Telegram ID (через API Proxy)
  fetchUser: async (telegram_id?: number) => {
    try {
      set({ loading: true, error: null })
      const data = await api.get<User>("/api/user/check", {
        params: { telegram_id },
      })
      get().setUser(data)
    } catch (e: any) {
      set({ error: e.response?.data?.error || "Ошибка загрузки", loading: false })
    }
  },

  // Метод 2: Загрузка по UUID токену (для входа по прямой ссылке)
  fetchBySubToken: async (token: string) => {
    try {
      set({ loading: true, error: null })
      const res = await api.get<any>("/api/auth/by-token", { params: { token } })

      if (res.session) {
        localStorage.setItem("session", res.session) // Сохраняем сессию!
      }

      if (res.django_first_user) {
        get().setUser(res.django_first_user) // Кладём "голого" юзера в стейт
      } else {
        set({ error: "Пользователь не найден", loading: false })
      }
    } catch (e: any) {
      set({ error: "Ошибка авторизации", loading: false })
    }
  },

  fetchTraffic: async () => {
    const { user } = get()
    if (!user?.telegram_id) return

    try {
      const res = await api.get<any>(`/api/user/full-stats`, {
        params: { telegram_id: user.telegram_id },
      })

      if (res && res.summary) {
        const { summary } = res
        const total = summary.total_lifetime_gb
        const used = summary.monthly_total_gb

        set({
          traffic: {
            usedGb: used.toFixed(2),
            totalGb: total.toFixed(0),
            percent: total > 0 ? Math.min(100, (used / total) * 100) : 0,
          },
        })
      }
    } catch (e: any) {
      console.error("[UserStore] Ошибка трафика:", e.message)
    }
  },

  setUser: (u) => {
    set({ user: u, loading: false, error: null })
    if (u) {
      localStorage.setItem("user", JSON.stringify(u))
      if (u.telegram_id) get().fetchTraffic()
    }
  },

  setError: (msg) => set({ error: msg, loading: false }),
  setLoading: (v) => set({ loading: v }),
  setInitData: (v) => set({ initData: v }),
}))
