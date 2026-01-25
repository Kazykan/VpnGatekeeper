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

  return (
    <Page>
      <Header user={user} session={session} />

      {/* Контент в зависимости от активного таба */}
      <div className="pb-24">
        {" "}
        {/* Отступ для таббара */}
        {activeTab === "vpn" && (
          <div className="animate-fadeIn">
            <UserInfo user={user} />
            <Payment />
            <Block
              strong
              inset
              className="text-center text-[10px] text-gray-500 uppercase tracking-widest opacity-60"
            >
              Безопасное соединение через протоколы VLESS/AmneziaWG
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
