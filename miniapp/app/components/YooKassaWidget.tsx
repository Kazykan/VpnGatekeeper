"use client"

import React, { useState } from "react"
import Script from "next/script"
import { Preloader } from "konsta/react"

// Типизация для окна браузера
declare global {
  interface Window {
    YooMoneyCheckoutWidget: any
  }
}

interface Props {
  confirmationToken: string
  onSuccess: () => void
  onError: (error: any) => void
}

const YooKassaWidget: React.FC<Props> = ({ confirmationToken, onSuccess, onError }) => {
  const [isLoaded, setIsLoaded] = useState(false)

  const initWidget = () => {
    if (typeof window !== "undefined" && window.YooMoneyCheckoutWidget) {
      try {
        const checkout = new window.YooMoneyCheckoutWidget({
          confirmation_token: confirmationToken,
          full_size: true,
          error_callback: (error: any) => {
            console.error("Yookassa Widget Error:", error)
            onError(error)
          },
        })

        checkout.on("success", () => {
          console.log("Payment success")
          onSuccess()
        })

        checkout.on("fail", () => {
          onError("Платеж отклонен")
        })

        checkout.render("payment-form")
        setIsLoaded(true)
      } catch (e) {
        console.error("Widget Init Error:", e)
        onError(e)
      }
    }
  }

  return (
    <div className="w-full bg-white flex flex-col items-center">
      {/* Используем компонент Script от Next.js */}
      <Script
        src="https://yookassa.ru/checkout-widget/v1/checkout-widget.js"
        strategy="afterInteractive"
        onLoad={initWidget}
        onError={() => onError("Не удалось загрузить скрипт оплаты")}
      />

      {!isLoaded && (
        <div className="flex flex-col items-center justify-center p-12">
          <Preloader className="mb-2" />
          <p className="text-sm text-gray-500">Загрузка формы оплаты...</p>
        </div>
      )}

      <div
        id="payment-form"
        className={`w-full min-h-[500px] transition-opacity duration-500 ${isLoaded ? "opacity-100" : "opacity-0"}`}
      />
    </div>
  )
}

export default YooKassaWidget
