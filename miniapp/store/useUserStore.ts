import { create } from "zustand"

export interface User {
  id: number
  name: string
  telegram_id: number
  end_date?: string | null
  invited_by?: number | null
  traffic_on: boolean
  autopay_enabled: boolean
}

interface UserStore {
  user: User | null
  loading: boolean
  error: string | null
  initData: string

  setUser: (u: User | null) => void
  setError: (msg: string) => void
  setLoading: (v: boolean) => void
  setInitData: (v: string) => void
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  loading: true,
  error: null,
  initData: "",

  setUser: (u) => set({ user: u, loading: false }),
  setError: (msg) => set({ error: msg, loading: false }),
  setLoading: (v) => set({ loading: v }),
  setInitData: (v) => set({ initData: v }),
}))
