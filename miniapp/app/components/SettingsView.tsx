"use client"

import { List, ListItem, Toggle, BlockTitle, Block } from "konsta/react"
import { MessageCircle, LifeBuoy } from "lucide-react"
import { User } from "@/app/types/user"

interface Props {
  user: User
}

export function SettingsView({ user }: Props) {
  const handleSupportClick = async () => {
    // 1. Отправляем "сигнал" админу через твой API
    try {
      await fetch("/api/user/support-click", { method: "POST" })
    } catch (e) {
      console.error("Failed to notify admin", e)
    }

    // 2. Открываем личку с тобой (замени @your_nickname на свой)
    window.open("https://t.me/Kazykan", "_blank")
  }

  const toggleAutopay = () => {
    // Здесь будет логика вызова API для включения/выключения
    console.log("Toggle autopay logic")
  }

  return (
    <div className="animate-fadeIn">
      <BlockTitle>Управление подпиской</BlockTitle>
      <List strong inset>
        <ListItem
          title="Автопродление"
          subtitle="Списание за 2 дня до конца"
          after={<Toggle checked={user.autopay_enabled} onChange={toggleAutopay} color="green" />}
        />
      </List>

      <BlockTitle>Поддержка и связь</BlockTitle>
      <List strong inset>
        <ListItem
          link
          title="Написать админу"
          subtitle="Если возникли проблемы"
          media={<MessageCircle className="text-primary" />}
          onClick={handleSupportClick}
        />
        <ListItem link title="Инструкции" media={<LifeBuoy />} />
      </List>

      <BlockTitle>Приложение</BlockTitle>
      <List strong inset>
        <ListItem title="Язык" after="Русский" />
        <ListItem title="Версия" after="2.1.0" />
      </List>

      <Block className="text-center opacity-40 text-[12px]">ID: {user.telegram_id}</Block>
    </div>
  )
}
