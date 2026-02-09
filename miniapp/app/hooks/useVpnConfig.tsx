"use client"

import { useState, useCallback, useEffect } from "react"
import { useUserStore } from "@/store/useUserStore"

// status204 → есть только старые конфиги (HTTP 204)
// status404 → пользователя нет / нет конфигов вообще (HTTP 404)
// fetchNewConfig → POST-запрос на генерацию нового конфига
export function useVpnConfig() {
  const { user } = useUserStore()

  const [configs, setConfigs] = useState<any[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [status204, setStatus204] = useState(false)
  const [status404, setStatus404] = useState(false)

  const loadConfig = useCallback(async () => {
    if (!user?.telegram_id) return

    setLoading(true)
    setError(null)
    setStatus204(false)
    setStatus404(false)

    try {
      const res = await fetch(`/api/credentials/config-by-tg?telegram_id=${user.telegram_id}`)

      console.log("[useVpnConfig] HTTP status:", res.status)

      if (res.status === 200) {
        const data = await res.json()
        setConfigs(data)
        return
      }

      if (res.status === 204) {
        setConfigs([])
        setStatus204(true)
        return
      }

      if (res.status === 404) {
        setConfigs([])
        setStatus404(true)
        return
      }

      // Любой другой статус
      const data = await res.json()
      setError(data?.error || "Неизвестная ошибка")
      setConfigs([])
    } catch (e) {
      console.error(e)
      setError("Ошибка загрузки конфигов")
      setConfigs([])
    } finally {
      setLoading(false)
    }
  }, [user?.telegram_id])

  // Генерация нового конфига
  const fetchNewConfig = useCallback(async () => {
    if (!user?.telegram_id) return

    setLoading(true)
    setError(null)

    try {
      const res = await fetch(
        `/api/credentials/generate-new-config?telegram_id=${user.telegram_id}`,
        { method: "POST" },
      )

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data?.error || "Не удалось сгенерировать конфиг")
      }

      alert("Новый конфиг сгенерирован. Старый перестал работать.")
      await loadConfig()
    } catch (e: any) {
      console.error(e)
      alert(e.message || "Ошибка при генерации нового конфига")
    } finally {
      setLoading(false)
    }
  }, [user?.telegram_id, loadConfig])

  useEffect(() => {
    loadConfig()
  }, [loadConfig])

  return {
    configs,
    loading,
    error,
    status204,
    status404,
    fetchNewConfig,
  }
}
