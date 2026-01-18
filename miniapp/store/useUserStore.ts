import { create } from "zustand"

export interface User {
  id: number
  first_name: string
  last_name?: string
  username?: string
}

interface UserStore {
  user: User | null
  loading: boolean
  error: string | null
  initData: string

  setUser: (u: User) => void
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
