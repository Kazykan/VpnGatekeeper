"use client"

import React, { useState } from "react"
import { useUserStore } from "@/store/useUserStore"
import { VpnConfigInline } from "./components/VpnConfigInline"
import { GlobeLock, Settings, Unplug } from "lucide-react"
import { Page, Block, Tabbar, TabbarLink, List, ListItem, Toggle, BlockTitle } from "konsta/react"
import { useSessionStore } from "@/store/useSessionStore"
import { RequireBotRegistration } from "./components/RequireBotRegistration"
import { Header } from "./components/Header"
import { UserInfo } from "./components/UserInfo"
import { TrafficStats } from "./components/TrafficStats"
import { ReferralCard } from "./components/ReferralCard"
import { SubscriptionStatus } from "./components/SubscriptionStatus"
import { ConnectAction } from "./components/ConnectAction"
import { SettingsView } from "./components/SettingsView"

export default function Home() {
  const [activeTab, setActiveTab] = useState("vpn")
  const { user, loading, error } = useUserStore()
  const session = useSessionStore((s) => s.session)

  // Обработка состояний загрузки и ошибок
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

  if (!user) {
    return (
      <Page>
        <Block>Ошибка: {error || "Пользователь не найден"}</Block>
      </Page>
    )
  }

  return (
    <Page>
      <Header user={user} session={session} />

      {/* Основной контент */}
      <div className="pb-24">
        {/* ТАБ: VPN (ГЛАВНАЯ) */}
        {activeTab === "vpn" && (
          <div className="animate-fadeIn">
            {" "}
            <UserInfo user={user} />
            {/* Этот компонент теперь сам решит: показать статус или форму оплаты */}
            <SubscriptionStatus user={user} />
            <ConnectAction onClick={() => setActiveTab("stats")} />
            <ReferralCard />
            <Block
              strong
              inset
              className="my-4! text-center text-2xs text-gray-500 uppercase tracking-[0.2em] opacity-40 font-bold"
            >
              Secure Protocol: VLESS
            </Block>
          </div>
        )}

        {/* ТАБ: ПОДКЛЮЧЕНИЕ (СТАТИСТИКА) */}
        {activeTab === "stats" && (
          <div className="animate-fadeIn">
            <BlockTitle>Подключение</BlockTitle>
            <VpnConfigInline />
            <TrafficStats />
          </div>
        )}

        {/* ТАБ: НАСТРОЙКИ */}
        {activeTab === "settings" && <SettingsView user={user} />}
      </div>

      {/* Таббар фиксированный снизу */}
      <Tabbar labels icons className="fixed left-0 bottom-0 w-full border-t border-gray-800">
        <TabbarLink
          active={activeTab === "vpn"}
          onClick={() => setActiveTab("vpn")}
          icon={<GlobeLock />}
          label="Главная"
        />
        <TabbarLink
          active={activeTab === "stats"}
          onClick={() => setActiveTab("stats")}
          icon={<Unplug />}
          label="Подключение"
        />
        <TabbarLink
          active={activeTab === "settings"}
          onClick={() => setActiveTab("settings")}
          icon={<Settings />}
          label="Настройки"
        />
      </Tabbar>
    </Page>
  )
}
