"use client"

import React, { useEffect } from "react"

// Описываем, что именно возвращает конструктор виджета
interface YookassaCheckoutInstance {
  render: (containerId: string) => void
  on: (event: string, callback: () => void) => void
  destroy: () => void
}

// Описываем структуру самого конструктора в объекте window
interface YooMoneyCheckoutWidgetConstructor {
  new (config: {
    confirmation_token: string
    full_size?: boolean
    error_callback?: (error: Error) => void
  }): YookassaCheckoutInstance
}

interface Props {
  confirmationToken: string
  onSuccess: () => void
  onError: (error: Error | string) => void // Типизируем ошибку
}

declare global {
  interface Window {
    YooMoneyCheckoutWidget: YooMoneyCheckoutWidgetConstructor
  }
}

const YooKassaWidget: React.FC<Props> = ({ confirmationToken, onSuccess, onError }) => {
  useEffect(() => {
    const initWidget = () => {
      if (window.YooMoneyCheckoutWidget) {
        const checkout = new window.YooMoneyCheckoutWidget({
          confirmation_token: confirmationToken,
          full_size: true,
          error_callback: (error: Error) => {
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

        checkout.render("payment-form")
      }
    }

    if (document.getElementById("yookassa-script")) {
      initWidget()
      return
    }

    const script = document.createElement("script")
    script.id = "yookassa-script"
    script.src = "https://yookassa.ru/checkout-widget/v1/checkout-widget.js"
    script.async = true
    script.onload = initWidget
    script.onerror = () => onError(new Error("Не удалось загрузить скрипт ЮKassa"))
    document.body.appendChild(script)
  }, [confirmationToken, onSuccess, onError]) // Добавили зависимости для линтера

  return (
    <div className="w-full bg-white p-2 rounded-lg">
      <div id="payment-form" className="min-h-[400px] w-full" />
    </div>
  )
}

export default YooKassaWidget
