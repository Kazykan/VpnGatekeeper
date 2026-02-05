"use client"

import { useState, useCallback } from "react"
import { useUserStore } from "@/store/useUserStore"

export function useVpnConfig() {
  const { user } = useUserStore()
  const [credential, setCredential] = useState<any | null>(null)
  const [config, setConfig] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Загружаем credentials пользователя
  const loadCredentials = useCallback(async () => {
    if (!user) {
      setError("User not loaded")
      return
    }

    try {
      setLoading(true)
      setError(null)

      const res = await fetch(`/api/credentials/list?user=${user.id}`)
      const data = await res.json()

      if (!Array.isArray(data) || data.length === 0) {
        setError("Credentials not found")
        return
      }

      // Берём первый активный credential
      const active = data.find((c: any) => c.active) || data[0]
      setCredential(active)
    } catch (e: any) {
      setError("Failed to load credentials")
    } finally {
      setLoading(false)
    }
  }, [user])

  // Загружаем config-urls
  const loadConfig = useCallback(async () => {
    if (!credential) {
      setError("Credential not loaded")
      return
    }

    try {
      setLoading(true)
      setError(null)

      const res = await fetch(`/api/credentials/${credential.id}/config-urls`)
      const data = await res.json()

      if (data.error) {
        setError(data.error)
        return
      }

      setConfig(data)
      return data
    } catch (e: any) {
      setError("Failed to load config")
    } finally {
      setLoading(false)
    }
  }, [credential])

  return {
    credential,
    config,
    loading,
    error,
    loadCredentials,
    loadConfig,
  }
}
