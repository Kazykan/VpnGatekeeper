"use client"

import React, { useEffect } from "react"

interface Props {
  confirmationToken: string
  onSuccess: () => void
  onError: (error: any) => void
}

declare global {
  interface Window {
    YooMoneyCheckoutWidget: any
  }
}

const YooKassaWidget: React.FC<Props> = ({ confirmationToken, onSuccess, onError }) => {
  useEffect(() => {
    // 1. Функция инициализации
    const initWidget = () => {
      if (window.YooMoneyCheckoutWidget) {
        const checkout = new window.YooMoneyCheckoutWidget({
          confirmation_token: confirmationToken,
          full_size: true, // виджет займет весь контейнер
          error_callback: (error: any) => {
            console.error("Yookassa Widget Error:", error)
            onError(error)
          },
        })

        checkout.on("success", () => {
          onSuccess()
        })

        checkout.on("fail", () => {
          onError(new Error("Payment failed"))
        })

        // Рендерим в div с id="payment-form"
        checkout.render("payment-form")
      }
    }

    // 2. Проверяем, загружен ли уже скрипт
    if (document.getElementById("yookassa-script")) {
      initWidget()
      return
    }

    // 3. Если нет — загружаем динамически
    const script = document.createElement("script")
    script.id = "yookassa-script"
    script.src = "https://yookassa.ru/checkout-widget/v1/checkout-widget.js"
    script.async = true
    script.onload = initWidget
    script.onerror = () => onError(new Error("Не удалось загрузить скрипт ЮKassa"))
    document.body.appendChild(script)

    return () => {
      // Очищать скрипт не обязательно, чтобы не загружать заново при смене тарифа
    }
  }, [confirmationToken])

  return (
    <div className="w-full bg-white p-2 rounded-lg">
      <div id="payment-form" className="min-h-[400px] w-full" />
    </div>
  )
}

export default YooKassaWidget
