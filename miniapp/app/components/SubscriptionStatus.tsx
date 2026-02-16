"use client"

import { Block } from "konsta/react"
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
    <Block strong inset className="!my-2 border-l-4 border-primary bg-primary/5">
      <div className="flex justify-between items-start mb-2">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider">Подписка активна</p>
          <p className="text-xl font-bold">Осталось: {daysLeft} дн.</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-gray-500 uppercase">До {endDate?.toLocaleDateString()}</p>
        </div>
      </div>

      {user.autopay_enabled && autopayDate && (
        <div className="mt-4 p-2 bg-black/20 rounded-lg flex items-center gap-2">
          <span className="text-lg">💳</span>
          <div className="text-[11px] leading-tight text-gray-300">
            Автопродление включено. Списание произойдет <br />
            <span className="text-primary font-semibold">
              {autopayDate.toLocaleDateString()}
            </span>{" "}
            (за 2 дня до конца)
          </div>
        </div>
      )}

      {!user.autopay_enabled && daysLeft <= 5 && (
        <div className="mt-4">
          <p className="text-[11px] text-orange-400 mb-2">
            Советуем продлить заранее, чтобы не потерять доступ
          </p>
          <Payment />
        </div>
      )}
    </Block>
  )
}
