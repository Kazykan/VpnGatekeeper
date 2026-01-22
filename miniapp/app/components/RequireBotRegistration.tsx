"use client"

import { Button, Block } from "konsta/react"

export function RequireBotRegistration() {
  const telegram_url = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/Kazykan_bot"
  const tg = window.Telegram?.WebApp
  const handleOpenBot = () => {
    const tg = window.Telegram?.WebApp
    if (tg) {
      // Нативный способ открыть ссылку внутри Telegram
      tg.openTelegramLink(telegram_url + "?start=check_vpn")
      tg.close()
    } else {
      // Резервный вариант для обычного браузера
      window.open(telegram_url, "_blank")
    }
  }
  return (
    <Block strong className="text-center">
      <p>Чтобы пользоваться сервисом, откройте бота {telegram_url}</p>
      <Button large onClick={handleOpenBot}>
        Открыть бота
      </Button>
    </Block>
  )
}
