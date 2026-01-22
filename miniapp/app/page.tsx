"use client"

import { useUserStore } from "@/store/useUserStore"
import { Page, Navbar, Block, Button, Tabbar, TabbarLink } from "konsta/react"
import { Avatar } from "./components/Avatar"
import { useSessionStore } from "@/store/useSessionStore"
import { RequireBotRegistration } from "./components/RequireBotRegistration"
import { Payment } from "./components/Payment"

export default function Home() {
  const { user, loading, error } = useUserStore()

  const session = useSessionStore((s) => s.session)

  // Если идет загрузка авторизации, показываем экран ожидания
  if (loading) {
    return (
      <Page className="flex items-center justify-center">
        <p>Загрузка данных Telegram...</p>
      </Page>
    )
  }

  if (error === "NOT_REGISTERED") {
    return <RequireBotRegistration />
  }
  if (!user) {
    return <p>Ошибка: {error}</p>
  }

  return (
    <Page className="h-screen pb-12">
      {" "}
      {/* Добавляем отступ снизу, чтобы контент не уходил под таббар */}
      <Navbar title="Rufat VPN" right={user && session && <Avatar user={user} />} />
      {/* Основной контент */}
      <div className="flex-1 overflow-y-auto">
        <Block strong>
          <p>Привет, {user.name}!</p>
          <p>Подписка до: {user.end_date}</p>
        </Block>

        {/* Вставляем блок оплаты */}
        <Payment />

        {/* Дополнительный блок для красоты */}
        <Block strong inset className="text-center text-xs text-gray-400">
          При нажатии на тариф вы перейдете в чат с ботом для оплаты через официальный платежный
          шлюз Telegram.
        </Block>
      </div>
      {/* Таббар теперь просто компонент внизу */}
      <Tabbar labels className="fixed left-0 bottom-0 w-full">
        <TabbarLink active icon={<span>🔒</span>} label="VPN" />
        <TabbarLink icon={<span>📊</span>} label="Статистика" />
        <TabbarLink icon={<span>⚙️</span>} label="Настройки" />
      </Tabbar>
    </Page>
  )
}
