"use client"
import { useState, useEffect, useMemo } from "react"
import { Block, Button, List, ListItem, Preloader, Segmented, SegmentedButton } from "konsta/react"
import { motion } from "framer-motion"
import { useUserStore } from "@/store/useUserStore"
import { Siren } from "lucide-react"

export function VpnConfigInline() {
  const { user, loading } = useUserStore()
  const [device, setDevice] = useState<"ios" | "android">("ios")

  useEffect(() => {
    const ua = navigator.userAgent.toLowerCase()
    if (/android/.test(ua)) setDevice("android")
  }, [])

  // 1. Проверка активности подписки с защитой от null/undefined
  const isSubscriptionActive = useMemo(() => {
    if (!user?.end_date) return false

    const now = new Date()
    now.setHours(0, 0, 0, 0)

    const endDate = new Date(user.end_date)
    // Если дата невалидна (Invalid Date), вернется false
    return !isNaN(endDate.getTime()) && endDate >= now
  }, [user?.end_date])

  // 2. Формирование ссылки с защитой
  const subscriptionUrl = useMemo(() => {
    if (!user?.sub_token) return ""
    const baseUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL || "https://api.yourdomain.com"
    const cleanBaseUrl = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl
    return `${cleanBaseUrl}/sub/${user.sub_token}/`
  }, [user?.sub_token])

  const copyToClipboard = (text: string, label: string) => {
    if (!text) return
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(() => alert(`✅ ${label} скопирована!`))
    } else {
      const textArea = document.createElement("textarea")
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand("copy")
        alert(`✅ ${label} скопирована!`)
      } catch (err) {
        alert("Ошибка при копировании")
      }
      document.body.removeChild(textArea)
    }
  }

  if (loading)
    return (
      <div className="flex justify-center p-12">
        <Preloader />
      </div>
    )

  // Показываем сообщение, если подписки нет или данные не загружены
  if (!user || !isSubscriptionActive || !user.sub_token) {
    return (
      <Block strong inset className="text-center py-8">
        <div className="text-4xl mb-4">
          <Siren />
        </div>
        <p className="opacity-60 text-sm">
          У вас нет активной подписки или срок её действия истек.
          <br />
          Пожалуйста, оплатите тариф, чтобы получить доступ.
        </p>
      </Block>
    )
  }

  // Для рендеринга даты используем безопасную переменную
  const formattedDate = user.end_date ? new Date(user.end_date).toLocaleDateString() : ""

  return (
    <div className="space-y-4 pb-20">
      <Block strong inset className="!mb-2">
        <Segmented raised>
          <SegmentedButton active={device === "ios"} onClick={() => setDevice("ios")}>
            iOS (iPhone)
          </SegmentedButton>
          <SegmentedButton active={device === "android"} onClick={() => setDevice("android")}>
            Android
          </SegmentedButton>
        </Segmented>
      </Block>

      <Block strong inset className="!my-2 border-l-4 border-primary bg-primary/5">
        <div className="text-[13px] space-y-3">
          <p className="font-bold text-sm text-primary">Инструкция по установке:</p>

          {device === "ios" ? (
            <div className="space-y-2">
              <p>
                1. Скачайте{" "}
                <a
                  href="https://apps.apple.com/tr/app/happ-proxy-utility/id6504287215"
                  target="_blank"
                  className="underline font-bold"
                >
                  Happ Proxy Utility
                </a>{" "}
                в App Store.
              </p>
              <p>
                2. Нажмите кнопку <span className="font-bold">"Копировать"</span> ниже.
              </p>
              <p>
                3. В приложении: <span className="font-bold text-primary">Из Буфера</span> →{" "}
                <span className="font-bold text-primary">"Вставить"</span>.
              </p>
              <p>
                4. Вставьте ссылку и нажмите <span className="font-bold">Done</span>.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <p>
                1. Установите{" "}
                <a
                  href="https://play.google.com/store/apps/details?id=com.happproxy&pcampaignid=web_share"
                  target="_blank"
                  className="underline font-bold"
                >
                  Happ - Proxy Utility
                </a>{" "}
                из Google Play.
              </p>
              <p>
                2. Нажмите кнопку <span className="font-bold">"Копировать"</span> ниже.
              </p>
              <p>
                3. В приложении: <span className="font-bold text-primary">Меню</span> →{" "}
                <span className="font-bold text-primary">Копировать из буфера</span> →{" "}
                <span className="font-bold text-primary">"+"</span>.
              </p>
              <p>
                4. Выберите <span className="font-bold text-primary">Импорт из буфера обмена</span>.
              </p>
            </div>
          )}
        </div>
      </Block>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <List strong inset className="!my-0">
          <ListItem
            title={<span className="text-sm font-bold">Ваша VPN подписка</span>}
            subtitle="Единая ссылка для подключения"
            after={
              <Button
                small
                raised
                className="ml-2"
                onClick={() => copyToClipboard(subscriptionUrl, "Ссылка подписки")}
              >
                Копировать
              </Button>
            }
          />
        </List>
        <div className="px-6 py-2 flex justify-between items-center text-[10px] text-gray-400 uppercase tracking-wider">
          <span>Статус: Активна</span>
          <span>До: {formattedDate}</span>
        </div>
      </motion.div>
    </div>
  )
}
