"use client"

import { Block, BlockTitle, Button } from "konsta/react"

export function Payment() {
  const handlePayment = (amount: number, type: string) => {
    const tg = window.Telegram?.WebApp
    const startParam = `pay_${amount}_${type}`
    const botUrl = `https://t.me/Kazykan_bot?start=${startParam}`

    if (tg) {
      tg.HapticFeedback?.impactOccurred("medium")
      tg.openTelegramLink(botUrl)
      setTimeout(() => {
        tg.close()
      }, 300)
    } else {
      window.open(botUrl, "_blank")
    }
  }

  return (
    <>
      <BlockTitle>Продлить подписку</BlockTitle>
      <Block strong className="space-y-3">
        {/* Кнопка без outline/clear — она будет основной (filled) */}
        <Button outline large onClick={() => handlePayment(80, "once")}>
          80₽ / 1 месяц
        </Button>

        {/* Основная кнопка с автопродлением */}
        <div className="py-1">
          <Button
            large
            // Убрали strong, так как его нет в типах Button
            // Кнопка по умолчанию будет с фоновым цветом (primary)
            className="h-16 shadow-lg"
            onClick={() => handlePayment(70, "sub")}
          >
            <div className="flex flex-col items-center justify-center leading-tight">
              <span className="font-bold text-lg">70₽ / месяц</span>
              <span className="text-2xs opacity-90 uppercase tracking-wider">
                Автопродление • Выгодно
              </span>
            </div>
          </Button>
        </div>

        <Button outline large onClick={() => handlePayment(210, "quarter")}>
          210₽ / 3 месяца
        </Button>
      </Block>
    </>
  )
}
