"use client"

import { useEffect, useRef } from "react"
import Script from "next/script"

type Props = {
  confirmationToken: string
  onSuccess?: () => void
  onError?: (error: any) => void
}

declare global {
  interface Window {
    YooMoneyCheckoutWidget: any
  }
}

export default function YooKassaWidget({ confirmationToken, onSuccess, onError }: Props) {
  const widgetRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!window.YooMoneyCheckoutWidget) return
    if (!confirmationToken) return

    try {
      const checkout = new window.YooMoneyCheckoutWidget({
        confirmation_token: confirmationToken,
        error_callback: (error: any) => {
          console.error("YooKassa error:", error)
          onError?.(error)
        },
        return_url: "https://t.me/your_bot",
      })

      checkout.render(widgetRef.current)

      checkout.on("success", () => {
        onSuccess?.()
      })
    } catch (e) {
      console.error("Widget init error:", e)
      onError?.(e)
    }
  }, [confirmationToken])

  return (
    <>
      {/* Надёжная загрузка скрипта */}
      <Script
        src="https://yookassa.ru/checkout-widget/v1/checkout-widget.js"
        strategy="afterInteractive"
        onLoad={() => console.log("YooKassa widget loaded")}
      />

      <div
        ref={widgetRef}
        style={{
          width: "100%",
          minHeight: "420px",
          display: "flex",
          justifyContent: "center",
        }}
      />
    </>
  )
}
