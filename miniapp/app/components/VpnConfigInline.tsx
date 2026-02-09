"use client"
import { useState, useEffect } from "react"
import { Block, Button, List, ListItem, Preloader, Segmented, SegmentedButton } from "konsta/react"
import { AnimatePresence, motion } from "framer-motion"
import { useVpnConfig } from "../hooks/VpnConfigInline"

export function VpnConfigInline() {
  const { configs, loading, status204, status404, fetchNewConfig } = useVpnConfig()
  const [device, setDevice] = useState<"ios" | "android">("ios")

  useEffect(() => {
    const ua = navigator.userAgent.toLowerCase()
    if (/android/.test(ua)) setDevice("android")
  }, [])

  // Улучшенная функция копирования с отладкой
  const copyToClipboard = (text: string | undefined, label: string) => {
    console.log(`[DEBUG] Попытка копирования ${label}:`, text)

    if (!text || text.trim() === "") {
      alert(`Ошибка: Данные для "${label}" отсутствуют в базе!`)
      return
    }

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard
        .writeText(text)
        .then(() => alert(`✅ ${label} скопирован!`))
        .catch(() => alert("Ошибка при копировании"))
    } else {
      // Резервный метод для некоторых мобильных браузеров
      const textArea = document.createElement("textarea")
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand("copy")
        alert(`✅ ${label} скопирован!`)
      } catch (err) {
        alert("Не удалось скопировать")
      }
      document.body.removeChild(textArea)
    }
  }

  if (loading)
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Preloader className="w-8 h-8" />
        <span className="text-sm opacity-50">Загрузка ключей...</span>
      </div>
    )

  // 404 — пользователь нет / нет конфигов вообще
  if (status404)
    return (
      <Block strong inset className="text-center opacity-60 text-sm">
        У вас пока нет активных подключений. Купите подписку, чтобы получить конфиг.
      </Block>
    )

  // 204 — есть только старые конфиги
  if (status204)
    return (
      <Block strong inset className="text-center opacity-60 text-sm space-y-2">
        <p>
          У вас есть только старые конфиги. Старый конфиг перестанет работать после генерации
          нового.
        </p>
        <Button
          raised
          onClick={() => {
            fetchNewConfig()
          }}
        >
          Получить новый конфиг
        </Button>
      </Block>
    )

  // configs есть → показываем как сейчас
  if (!configs || configs.length === 0)
    return (
      <Block strong inset className="text-center opacity-60 text-sm">
        У вас пока нет активных подключений.
      </Block>
    )

  return (
    <div className="space-y-4 pb-20">
      {/* Выбор устройства */}
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

      {/* Инструкция */}
      <Block strong inset className="!my-2 border-l-4 border-primary bg-primary/5">
        <div className="text-xs space-y-2">
          <p>
            <span className="font-bold">1. Установите:</span>{" "}
            {device === "ios" ? (
              <a
                href="https://apps.apple.com/app/defaultvpn/id6472635449"
                className="text-primary underline"
              >
                DefaultVPN
              </a>
            ) : (
              <a
                href="https://play.google.com/store/apps/details?id=org.amnezia.vpn"
                className="text-primary underline"
              >
                Amnezia VPN
              </a>
            )}
          </p>
          <p>
            <span className="font-bold">2. Скопируйте</span> конфиг кнопкой ниже.
          </p>
          <p>
            <span className="font-bold">3. Откройте</span> приложение и нажмите{" "}
            <span className="font-bold text-primary">+ (Добавить)</span>.
          </p>
        </div>
      </Block>

      <AnimatePresence>
        {configs.map((cred, idx) => (
          <motion.div
            key={cred.credential_id || idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-1"
          >
            <div className="px-5 text-[10px] uppercase text-gray-500 font-bold tracking-widest">
              Подключение #{idx + 1}
            </div>

            <List strong inset className="!my-0">
              {/* Основной - Швеция */}
              <ListItem
                title={<span className="text-sm font-bold">🇸🇪 Основной (Швеция)</span>}
                subtitle="WireGuard • Лучшая скорость"
                after={
                  <Button
                    small
                    clear
                    onClick={() =>
                      copyToClipboard(cred.configs?.main_wg?.config_text, "Основной конфиг")
                    }
                  >
                    Копия
                  </Button>
                }
              />

              {/* Резервный - Германия (VLESS) */}
              <ListItem
                title={<span className="text-sm font-bold">🇩🇪 Резервный (Германия)</span>}
                subtitle="VLESS • Обход блокировок"
                after={
                  <Button
                    small
                    clear
                    onClick={() => copyToClipboard(cred.configs?.vless?.link, "VLESS ссылку")}
                  >
                    Копия
                  </Button>
                }
              />

              {/* Whitelist */}
              <ListItem
                title={<span className="text-sm font-bold">🛡️ Только соцсети / Белые списки</span>}
                subtitle="Экономия трафика"
                after={
                  <Button
                    small
                    clear
                    onClick={() =>
                      copyToClipboard(cred.configs?.whitelist_wg?.config_text, "Whitelist конфиг")
                    }
                  >
                    Копия
                  </Button>
                }
              />
            </List>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
