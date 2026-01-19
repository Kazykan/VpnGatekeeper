"use client"

import { useEffect } from "react"
import { useUserStore } from "@/store/useUserStore"
import { useSessionStore } from "@/store/useSessionStore"

export default function InitTelegram() {
  const setUser = useUserStore((s) => s.setUser)
  const setError = useUserStore((s) => s.setError)
  const setLoading = useUserStore((s) => s.setLoading)
  const setSession = useSessionStore((s) => s.setSession)

  useEffect(() => {
    const tg = window.Telegram?.WebApp

    if (!tg) {
      setError("Telegram WebApp API недоступен")
      return
    }

    tg.ready()
    tg.expand()

    const savedSession = localStorage.getItem("session")
    const savedUser = localStorage.getItem("user")

    const authorize = async () => {
      const initData = tg.initData
      if (!initData) {
        setError("Откройте Mini App внутри Telegram")
        setLoading(false)
        return
      }

      setLoading(true)
      try {
        const r = await fetch("/api/auth/telegram/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ initData }),
        })

        const data = await r.json()
        console.log("API Response:", data) // <-- ШАГ 2: Что ответил Next.js?

        if (!r.ok || !data.session) {
          setError(data.error || "Ошибка авторизации")
          return
        }

        // Сохраняем сессию (токен Redis)
        localStorage.setItem("session", data.session)
        setSession(data.session)

        // Проверяем, вернул ли Django пользователя
        if (data.django_first_user) {
          console.log("User found:", data.django_first_user) // <-- ШАГ 3: Пришел ли юзер?
          localStorage.setItem("user", JSON.stringify(data.django_first_user))
          setUser(data.django_first_user)
        } else {
          // Если ok: true, но пользователя в БД нет
          setError("NOT_REGISTERED")
          setUser(null)
        }
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    // Если есть кэш, доверяем ему временно, но фоново проверяем
    if (savedSession && savedUser) {
      setSession(savedSession)
      setUser(JSON.parse(savedUser))
      setLoading(false)

      // Можно добавить фоновую валидацию здесь, если нужно
    } else {
      authorize()
    }
  }, [setUser, setError, setLoading, setSession])

  return null
}
