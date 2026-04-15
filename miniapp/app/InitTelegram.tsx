"use client"

import { useEffect, useRef } from "react"
import { useUserStore } from "@/store/useUserStore"
import { useSessionStore } from "@/store/useSessionStore"
import { useParams } from "next/navigation"

export default function InitTelegram() {
  const { setUser, setError, setLoading, fetchBySubToken, fetchUser } = useUserStore()
  const setSession = useSessionStore((s) => s.setSession)
  const params = useParams()
  const initialized = useRef(false)

  useEffect(() => {
    if (initialized.current) return

    const subToken = params?.token
    const tg = typeof window !== "undefined" ? window.Telegram?.WebApp : null

    const runInit = async () => {
      // 1. Сначала подтягиваем всё из кэша для мгновенного отображения
      const savedUser = localStorage.getItem("user")
      const savedSession = localStorage.getItem("session")
      if (savedUser) setUser(JSON.parse(savedUser))
      if (savedSession) setSession(savedSession)

      // 2. ПРИОРИТЕТ: Вход по UUID (ссылка /pay/...)
      if (subToken) {
        await fetchBySubToken(subToken as string)
        initialized.current = true
        return
      }

      // 3. СТАНДАРТ: Telegram Mini App
      if (tg && tg.initData) {
        tg.ready()
        tg.expand()

        try {
          const r = await fetch("/api/auth/telegram/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ initData: tg.initData }),
          })
          const data = await r.json()

          if (data.session && data.django_first_user) {
            localStorage.setItem("session", data.session)
            localStorage.setItem("user", JSON.stringify(data.django_first_user))
            setSession(data.session)
            setUser(data.django_first_user) // Обновит данные поверх кэша
          }
        } catch (e) {
          console.error("Auth error:", e)
        } finally {
          setLoading(false)
        }
      } else if (savedUser) {
        // 4. Если нет ТГ, но есть кэш — пробуем обновить данные юзера в фоне
        const userObj = JSON.parse(savedUser)
        if (userObj.telegram_id) {
          fetchUser(userObj.telegram_id) // Фоновое обновление
        }
        setLoading(false)
      } else {
        setError("Доступ запрещен")
        setLoading(false)
      }
      initialized.current = true
    }

    runInit()
  }, [params?.token])

  return null
}
