import { User } from "@/app/types/user"
import { api } from "@/lib/api"
import { create } from "zustand"
import axios from "axios"

export interface TrafficData {
  usedGb: string
  totalGb: string
  percent: number
  details?: any[] // Добавим для расширенной статистики, если нужно
}

interface UserStore {
  user: User | null
  traffic: TrafficData | null
  loading: boolean
  error: string | null
  initData: string

  fetchUser: (telegram_id?: number) => Promise<void>
  fetchTraffic: () => Promise<void>
  setUser: (u: User | null) => void
  setError: (msg: string) => void
  setLoading: (v: boolean) => void
  setInitData: (v: string) => void
}

export const useUserStore = create<UserStore>((set, get) => ({
  user: null,
  traffic: null,
  loading: true,
  error: null,
  initData: "",

  fetchUser: async (telegram_id?: number) => {
    try {
      set({ loading: true })
      // Запрашиваем через наш Next.js API Proxy
      const data = await api.get<User>("/api/user/check", {
        params: { telegram_id },
      })
      get().setUser(data)
    } catch (e: any) {
      set({ error: e.response?.data?.error || "Ошибка загрузки" })
    } finally {
      set({ loading: false })
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
      console.error("[TrafficStore] Ошибка загрузки:", e.message)
    }
  },

  setUser: (u) => {
    set({ user: u, loading: false })
    // Если юзер найден — тянем трафик
    if (u?.telegram_id) {
      get().fetchTraffic()
    }
  },

  setError: (msg) => set({ error: msg, loading: false }),
  setLoading: (v) => set({ loading: v }),
  setInitData: (v) => set({ initData: v }),
}))
