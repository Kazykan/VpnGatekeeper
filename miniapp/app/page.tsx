"use client"

import React, { useState } from "react"
import { useUserStore } from "@/store/useUserStore"
import {
  Page,
  Block,
  Tabbar,
  TabbarLink,
  Icon,
  List,
  ListItem,
  Toggle,
  BlockTitle,
} from "konsta/react"
import { useSessionStore } from "@/store/useSessionStore"
import { RequireBotRegistration } from "./components/RequireBotRegistration"
import { Payment } from "./components/Payment"
import { Header } from "./components/Header"
import { UserInfo } from "./components/UserInfo"

export default function Home() {
  const [activeTab, setActiveTab] = useState("vpn")
  const { user, loading, error } = useUserStore()
  const session = useSessionStore((s) => s.session)

  if (loading) {
    return (
      <Page className="flex items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="text-sm opacity-50">Загрузка данных...</p>
        </div>
      </Page>
    )
  }

  if (error === "NOT_REGISTERED") return <RequireBotRegistration />
  if (!user)
    return (
      <Page>
        <Block>Ошибка: {error}</Block>
      </Page>
    )

  // Рассчитываем остаток дней
  const now = new Date()
  const endDate = user.end_date ? new Date(user.end_date) : null
  const daysLeft = endDate
    ? Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
    : 0

  const isSubscriptionActive = daysLeft > 0

  // Дата автосписания (за 2 дня до окончания)
  const autopayDate = endDate ? new Date(endDate.getTime() - 2 * 24 * 60 * 60 * 1000) : null

  return (
    <Page>
      <Header user={user} session={session} />

      {/* Контент в зависимости от активного таба */}
      <div className="pb-24">
        {" "}
        {/* Отступ для таббара */}
        {activeTab === "vpn" && (
          <div className="animate-fadeIn space-y-4">
            <UserInfo user={user} />

            {isSubscriptionActive ? (
              <Block strong inset className="!my-2 border-l-4 border-primary bg-primary/5">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">
                      Подписка активна
                    </p>
                    <p className="text-xl font-bold">Осталось: {daysLeft} дн.</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-gray-500 uppercase">
                      До {endDate?.toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {user.autopay_enabled && autopayDate && (
                  <div className="mt-4 p-2 bg-black/20 rounded-lg flex items-center gap-2">
                    <span className="text-lg">💳</span>
                    <div className="text-[11px] leading-tight text-gray-300">
                      Автопродление включено. Списание произойдет <br />
                      <span className="text-primary font-semibold">
                        {autopayDate.toLocaleDateString()}
                      </span>{" "}
                      (за 2 дня до конца)
                    </div>
                  </div>
                )}

                {/* Если дней осталось мало, а автооплаты нет — можно все же показать кнопку продления */}
                {!user.autopay_enabled && daysLeft <= 5 && (
                  <div className="mt-4">
                    <p className="text-[11px] text-orange-400 mb-2">
                      Советуем продлить заранее, чтобы не потерять доступ
                    </p>
                    <Payment small /> {/* Можно сделать Payment компактным через пропсы */}
                  </div>
                )}
              </Block>
            ) : (
              <Payment />
            )}

            {/* Блок с трафиком (статистика) */}
            <Block strong inset className="!my-2">
              <div className="flex justify-between items-end mb-1">
                <span className="text-xs text-gray-400">Использовано за месяц</span>
                <span className="text-sm font-mono">12.4 GB / ∞</span>
              </div>
              <div className="w-full bg-gray-800 h-1 rounded-full">
                <div className="bg-primary h-full w-[12%]" />
              </div>
            </Block>

            <Block
              strong
              inset
              className="text-center text-[10px] text-gray-500 uppercase tracking-widest opacity-60"
            >
              Протоколы: VLESS + AmneziaWG
            </Block>
          </div>
        )}
        {activeTab === "stats" && (
          <div className="animate-fadeIn">
            <BlockTitle>Ваша статистика</BlockTitle>
            <Block strong inset className="space-y-4">
              <div className="flex justify-between items-center border-b border-gray-800 pb-2">
                <span className="text-gray-400">Использовано трафика</span>
                <span className="font-mono text-primary">12.4 GB</span>
              </div>
              <div className="flex justify-between items-center border-b border-gray-800 pb-2">
                <span className="text-gray-400">Дней в сети</span>
                <span className="font-mono text-primary">24 дня</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Статус узла</span>
                <span className="text-green-500 flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span> Online
                </span>
              </div>
            </Block>
            <Block className="text-sm text-gray-400 italic">
              * Статистика обновляется раз в 15 минут
            </Block>
          </div>
        )}
        {activeTab === "settings" && (
          <div className="animate-fadeIn">
            <BlockTitle>Настройки приложения</BlockTitle>
            <List strong inset>
              <ListItem title="Уведомления" after={<Toggle defaultChecked small color="green" />} />
              <ListItem
                title="Smart Mode"
                subtitle="Автоматический выбор сервера"
                after={<Toggle small />}
              />
            </List>
            <List strong inset>
              <ListItem title="Язык" after="Русский" link />
              <ListItem title="Помощь и поддержка" link />
              <ListItem title="Версия ПО" after="2.1.0" />
            </List>
          </div>
        )}
      </div>

      {/* Таббар фиксированный снизу */}
      <Tabbar labels icons className="fixed left-0 bottom-0 w-full border-t border-gray-800">
        <TabbarLink
          active={activeTab === "vpn"}
          onClick={() => setActiveTab("vpn")}
          icon={<span className="text-2xl">🛡️</span>}
          label="VPN"
        />
        <TabbarLink
          active={activeTab === "stats"}
          onClick={() => setActiveTab("stats")}
          icon={<span className="text-2xl">📈</span>}
          label="Статистика"
        />
        <TabbarLink
          active={activeTab === "settings"}
          onClick={() => setActiveTab("settings")}
          icon={<span className="text-2xl">⚙️</span>}
          label="Настройки"
        />
      </Tabbar>
    </Page>
  )
}
