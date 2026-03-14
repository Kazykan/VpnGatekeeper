"use client"

import { useState } from "react"
import {
  List,
  ListItem,
  Toggle,
  BlockTitle,
  Block,
  Dialog,
  DialogButton,
  Preloader,
} from "konsta/react"
import { MessageCircle, LifeBuoy, CreditCard, Trash2 } from "lucide-react"
import { User } from "@/app/types/user"
import { api } from "@/lib/api"
import { useUserStore } from "@/store/useUserStore"

interface Props {
  user: User
}

export function SettingsView({ user }: Props) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const fetchUser = useUserStore((s) => s.fetchUser)

  const handleUnbind = async () => {
    setLoading(true)
    try {
      // Идем через наш Next.js API Proxy
      await api.post("/api/payments/unbind-card", {
        telegram_id: user.telegram_id,
      })

      // Обновляем глобальный стор, чтобы данные синхронизировались
      await fetchUser(user.telegram_id)
      setShowConfirm(false)
    } catch (e) {
      console.error("Unbind error:", e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fadeIn">
      <BlockTitle>Управление подпиской</BlockTitle>
      <List strong inset>
        {/* Кнопка отвязки — показываем только если есть сохраненный метод */}
        {user.payment_method_id && (
          <>
            <ListItem
              title="Привязанная карта"
              // Выводим маску, если она прилетела из базы, иначе просто общий текст
              after={user.card_last4 ? `**** ${user.card_last4}` : "Банковская карта"}
              media={<CreditCard className="w-5 h-5 text-gray-500" />}
            />
            <ListItem
              link
              title={<span className="text-red-500">Отвязать карту</span>}
              media={<Trash2 className="text-red-500 w-5 h-5" />}
              onClick={() => setShowConfirm(true)}
            />
          </>
        )}

        <ListItem
          title="Автопродление"
          subtitle={user.payment_method_id ? "Списание за 2 дня до конца" : "Карта не привязана"}
          after={
            <Toggle
              checked={user.autopay_enabled}
              // Если карты нет, тумблер просто неактивен
              onChange={() => user.payment_method_id && setShowConfirm(true)}
              disabled={!user.payment_method_id}
              color="green"
            />
          }
        />
      </List>

      <BlockTitle>Поддержка и связь</BlockTitle>
      <List strong inset>
        <ListItem
          link
          title="Написать админу"
          media={<MessageCircle className="text-primary" />}
          onClick={() => window.open("https://t.me/Kazykan", "_blank")}
        />
        <ListItem link title="Инструкции" media={<LifeBuoy />} />
      </List>

      <Block className="text-center opacity-40 text-[12px] mt-4">ID: {user.telegram_id}</Block>

      <Dialog
        opened={showConfirm}
        onBackdropClick={() => !loading && setShowConfirm(false)}
        title="Удалить карту?"
        content="Автопродление будет отключено, а данные карты стерты."
        buttons={
          <>
            <DialogButton onClick={() => setShowConfirm(false)} disabled={loading}>
              Отмена
            </DialogButton>
            <DialogButton onClick={handleUnbind} className="text-red-500">
              {loading ? <Preloader className="w-5 h-5" /> : "Удалить"}
            </DialogButton>
          </>
        }
      />
    </div>
  )
}
