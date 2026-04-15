"use client"

import { useEffect, useRef } from "react"
import { useUserStore } from "@/store/useUserStore"
import { useSessionStore } from "@/store/useSessionStore"
import { useParams } from "next/navigation"

export default function InitTelegram() {
  const { setUser, setError, setLoading, fetchBySubToken } = useUserStore()
  const setSession = useSessionStore((s) => s.setSession)
  const params = useParams()

  // Используем ref, чтобы запрос не улетал дважды при React Strict Mode
  const initialized = useRef(false)

  useEffect(() => {
    if (initialized.current) return

    const subToken = params?.token
    const tg = typeof window !== "undefined" ? window.Telegram?.WebApp : null

    // 1. ПРИОРИТЕТ: Вход по UUID (Прямая ссылка)
    // Если токен есть, сразу идем за данными и не ждем ничего другого
    if (subToken) {
      console.log("🛠 Init by Token:", subToken)
      fetchBySubToken(subToken as string)
      initialized.current = true
      return
    }

    // 2. СТАНДАРТ: Telegram Mini App
    if (tg && tg.initData) {
      console.log("🛠 Init by Telegram")
      tg.ready()
      tg.expand()

      const authorize = async () => {
        // Оптимистичный UI: грузим из кеша
        const savedUser = localStorage.getItem("user")
        if (savedUser) setUser(JSON.parse(savedUser))

        try {
          const r = await fetch("/api/auth/telegram/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ initData: tg.initData }),
          })
          const data = await r.json()

          if (data.session) {
            localStorage.setItem("session", data.session)
            setSession(data.session)
            if (data.django_first_user) setUser(data.django_first_user)
          }
        } catch (e) {
          setError("Ошибка сети")
        } finally {
          setLoading(false)
        }
      }

      authorize()
      initialized.current = true
    } else {
      // 3. ПРОВЕРКА КЕША (если просто открыли сайт)
      const savedUser = localStorage.getItem("user")
      if (savedUser) {
        setUser(JSON.parse(savedUser))
        setLoading(false)
        initialized.current = true
      }
    }
  }, [params?.token]) // Убираем лишние зависимости, оставляем только триггер по URL

  return null
}
