"use client"

import { App } from "konsta/react"
import "../app/globals.css"
import InitTelegram from "./InitTelegram"
import Script from "next/script"
import { ReactNode } from "react"

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru" className="dark" suppressHydrationWarning>
      <body className="bg-black">
        <Script src="https://telegram.org/js/telegram-web-app.js?56" strategy="beforeInteractive" />
        {/* <Script
          src="https://yookassa.ru/checkout-widget/v1/checkout-widget.js"
          strategy="beforeInteractive"
        /> */}
        <App theme="ios" dark={true}>
          <InitTelegram />
          {children}
        </App>
      </body>
    </html>
  )
}
