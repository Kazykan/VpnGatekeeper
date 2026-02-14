"use client"
import { Block, Button } from "konsta/react"
import { useUserStore } from "@/store/useUserStore"
import { motion } from "framer-motion"
import { useState } from "react"
// Импортируем иконки
import { UserPlus, Copy, Check } from "lucide-react"

export function ReferralCard() {
  const { user } = useUserStore()
  const [copied, setCopied] = useState(false)

  if (!user || user.end_date === null) return null

  const botUrl = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/Kazykan_bot"
  const referralLink = `${botUrl}?start=inv_${user.telegram_id}`

  const handleShare = () => {
    const tg = window.Telegram?.WebApp
    const shareText = "Получи качественный Интернет! По моей ссылке при регистрации дают бонусы."
    const fullShareUrl = `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent(shareText)}`

    if (tg?.openTelegramLink) {
      tg.openTelegramLink(fullShareUrl)
    } else {
      window.open(fullShareUrl, "_blank")
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(referralLink)
      setCopied(true)
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred("success")
      setTimeout(() => setCopied(false), 2000)
    } catch (e) {
      console.error("Copy failed", e)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Block strong inset className="!my-4 !p-0 overflow-hidden border-2 border-primary/20">
        <div className="bg-gradient-to-r from-primary to-purple-600 p-4 text-white">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-[10px] uppercase font-black opacity-80 tracking-tighter">Акция</p>
              <h3 className="text-xl font-bold leading-none">+20 ДНЕЙ</h3>
            </div>
            <div className="bg-white/20 backdrop-blur-md rounded-lg p-2 text-[10px] font-bold text-center leading-tight">
              ЗА КАЖДОГО
              <br />
              ДРУГА
            </div>
          </div>
        </div>

        <div className="p-4 space-y-4">
          <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed">
            Ваш друг получит доступ, а вы —{" "}
            <span className="text-primary font-bold">20 дней подписки</span> в подарок после его
            первой покупки.
          </p>

          <div className="flex gap-2">
            <Button
              rounded
              className="flex-1 !bg-primary active:opacity-80 transition-opacity flex items-center justify-center gap-2"
              onClick={handleShare}
            >
              {/* Иконка добавления пользователя */}
              <UserPlus size={18} strokeWidth={2.5} />
              <span>Пригласить</span>
            </Button>

            <Button
              rounded
              outline
              className="w-24 border-primary text-primary flex items-center justify-center gap-2"
              onClick={handleCopy}
            >
              {/* Анимированная смена иконки при копировании */}
              {copied ? (
                <Check size={18} strokeWidth={2.5} />
              ) : (
                <Copy size={18} strokeWidth={2.5} />
              )}
              <span>{copied ? "ОК" : "Копия"}</span>
            </Button>
          </div>

          <div className="px-3 py-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-dashed border-gray-200 dark:border-gray-800">
            <p className="text-[9px] font-mono text-gray-400 truncate text-center select-all">
              {referralLink}
            </p>
          </div>
        </div>
      </Block>
    </motion.div>
  )
}
