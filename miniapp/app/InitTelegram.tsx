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

    // Функция для выполнения чистой авторизации через Telegram InitData
    const authorize = async () => {
      const initData = tg.initData
      if (!initData) {
        setError("Открыть в Telegram")
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

        if (data.session && data.user) {
          localStorage.setItem("session", data.session)
          localStorage.setItem("user", JSON.stringify(data.user))
          setSession(data.session)
          setUser(data.user)
        } else {
          setError("Ошибка авторизации")
        }
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    // ЛОГИКА ПРОВЕРКИ:
    if (savedSession && savedUser) {
      // 1. Предварительно ставим данные из кэша, чтобы интерфейс не моргал
      setSession(savedSession)
      setUser(JSON.parse(savedUser))

      // 2. Проверяем, жива ли сессия на сервере (делаем легкий запрос)
      fetch(`/api/user/photo?user_id=${JSON.parse(savedUser).id}`, {
        headers: { Authorization: `Bearer ${savedSession}` },
      })
        .then((res) => {
          if (res.status === 401) {
            console.warn("Сессия истекла в Redis, переавторизация...")
            localStorage.removeItem("session")
            localStorage.removeItem("user")
            authorize() // Сессия протухла — логинимся заново
          } else {
            setLoading(false) // Всё ок, сессия валидна
          }
        })
        .catch(() => {
          setLoading(false) // Ошибка сети, оставляем как есть
        })
    } else {
      // Данных в кэше нет — логинимся сразу
      authorize()
    }
  }, [setUser, setError, setLoading, setSession])

  return null
}
