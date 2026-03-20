"use client"

import { Block, BlockTitle } from "konsta/react"
import { Payment } from "./Payment"
import { User } from "@/app/types/user"

interface Props {
  user: User
}

export function SubscriptionStatus({ user }: Props) {
  // 1. Вся логика расчетов теперь живет здесь, а не в Home
  const now = new Date()
  const endDate = user.end_date ? new Date(user.end_date) : null
  const daysLeft = endDate
    ? Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
    : 0

  const isSubscriptionActive = daysLeft > 0
  const autopayDate = endDate ? new Date(endDate.getTime() - 2 * 24 * 60 * 60 * 1000) : null

  // 2. Если подписка истекла, возвращаем компонент оплаты
  if (!isSubscriptionActive) {
    return <Payment />
  }

  // 3. Если активна — показываем статус
  return (
    <>
      <Block strong inset className="!my-2 border-l-4 border-primary bg-primary/5">
        <div className="flex justify-between items-start mb-2 font-sans">
          <div>
            <p className="text-[10px] text-gray-400 uppercase tracking-widest">Статус услуги</p>
            <p className="text-xl font-bold">Осталось: {daysLeft} дн.</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-gray-500 uppercase tracking-tighter">
              До {endDate?.toLocaleDateString()}
            </p>
          </div>
        </div>

        {user.autopay_enabled && autopayDate && (
          <div className="mt-4 p-3 bg-black/5 rounded-xl flex items-center gap-3">
            <span className="text-lg opacity-50 font-sans">💳</span>
            <div className="text-[11px] leading-tight text-gray-500 font-sans">
              Автопродление активно. Списание: <br />
              <span className="text-primary font-bold">{autopayDate.toLocaleDateString()}</span>
            </div>
          </div>
        )}
      </Block>

      {/* ИЗМЕНЕНО: Если дней мало, Payment рендерится ПОД блоком статуса, а не внутри него */}
      {!user.autopay_enabled && daysLeft <= 5 && (
        <div className="animate-fadeIn">
          <BlockTitle className="!mt-4 !mb-1 uppercase text-[10px] opacity-50 px-4">
            Рекомендуем продлить
          </BlockTitle>
          <Payment />
        </div>
      )}
    </>
  )
}
