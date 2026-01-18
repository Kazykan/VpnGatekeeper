import { create } from "zustand"

interface SessionState {
  session: string | null
  setSession: (s: string) => void
}

export const useSessionStore = create<SessionState>((set) => ({
  session: null,
  setSession: (s) => set({ session: s }),
}))
