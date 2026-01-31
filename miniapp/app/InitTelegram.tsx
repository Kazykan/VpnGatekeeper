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

    // Сообщаем Telegram, что приложение готово, и разворачиваем на всю высоту
    tg.ready()
    tg.expand()

    const authorize = async () => {
      const initData = tg.initData
      if (!initData) {
        setError("Откройте Mini App внутри Telegram")
        setLoading(false)
        return
      }

      // Если в стейте еще нет юзера (первая загрузка без кэша), включаем лоадер
      // Если юзер уже есть (из кэша), лоадер не показываем, обновление пройдет фоном
      const currentUser = useUserStore.getState().user
      if (!currentUser) setLoading(true)

      try {
        const r = await fetch("/api/auth/telegram/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ initData }),
        })

        const data = await r.json()

        if (!r.ok || !data.session) {
          setError(data.error || "Ошибка авторизации")
          return
        }

        // Обновляем сессию и кэш сессии
        localStorage.setItem("session", data.session)
        setSession(data.session)

        if (data.django_first_user) {
          // ВАЖНО: Перезаписываем localStorage свежими данными из БД (новая дата подписки)
          localStorage.setItem("user", JSON.stringify(data.django_first_user))
          // Обновляем глобальный стейт — интерфейс перерисуется с новой датой
          setUser(data.django_first_user)
        } else {
          setError("NOT_REGISTERED")
          setUser(null)
        }
      } catch (e: any) {
        console.error("Auth error:", e)
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    // --- ЛОГИКА СТРАТЕГИИ SWR (Stale-While-Revalidate) ---

    const savedSession = localStorage.getItem("session")
    const savedUser = localStorage.getItem("user")

    // 1. Если есть старые данные, мгновенно подставляем их в UI
    if (savedSession && savedUser) {
      setSession(savedSession)
      setUser(JSON.parse(savedUser))
      // Мы не вызываем setLoading(false) здесь преждевременно,
      // чтобы дождаться конца фоновой проверки, если это нужно.
      // Но в данном случае authorize() сам разберется с setLoading.
    }

    // 2. В ЛЮБОМ СЛУЧАЕ идем на сервер за актуальными данными.
    // Это решит проблему со старой датой: даже если юзер видит старую дату секунду,
    // она обновится сразу после завершения fetch.
    authorize()
  }, [setUser, setError, setLoading, setSession])

  return null
}
