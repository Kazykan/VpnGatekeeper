"use client"

import { Button, Block } from "konsta/react"

export function RequireBotRegistration() {
  const telegram_url = "https://t.me/" + process.env.TELEGRAM_BOT_URL
  return (
    <Block strong className="text-center">
      <p>Чтобы пользоваться сервисом, откройте бота</p>
      <Button
        large
        onClick={() => {
          window.location.href = telegram_url
        }}
      >
        Открыть бота
      </Button>
    </Block>
  )
}
