// hooks/useVpnConfig.tsx
"use client"
import { useState, useCallback, useEffect } from "react"
import { useUserStore } from "@/store/useUserStore"

export function useVpnConfig() {
  const { user } = useUserStore()
  const [configs, setConfigs] = useState<any[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadConfig = useCallback(async () => {
    if (!user?.telegram_id) return
    try {
      setLoading(true)
      const res = await fetch(`/api/credentials/config-by-tg?telegram_id=${user.telegram_id}`)
      const data = await res.json()

      // ЛОГ №2: Что прилетело в браузер
      console.log(" [HOOK] Данные из API:", data)
      // API возвращает массив [{ credential_id, configs: {...} }, ...]
      setConfigs(data)
    } catch (e) {
      setError("Ошибка загрузки")
    } finally {
      setLoading(false)
    }
  }, [user?.id])

  useEffect(() => {
    loadConfig()
  }, [loadConfig])

  return { configs, loading, error }
}
