"use client"

import { Block } from "konsta/react"
import { User } from "../types/user"

export function UserInfo({ user }: { user: User }) {
  // 1. Проверяем, есть ли дата вообще
  const hasDate = Boolean(user.end_date)

  // 2. Если даты нет, считаем подписку неактивной (или по вашей логике)
  // Используем "!" или проверку, чтобы успокоить TS
  const endDate = hasDate ? new Date(user.end_date!) : null
  const now = new Date()

  // 3. Подписка истекла, если даты нет ИЛИ она меньше текущей
  const isExpired = !endDate || endDate < now

  // Если дата окончания МЕНЬШЕ текущей — подписка истекла
  const isSubscriptionExpired = !endDate || endDate.getTime() < now.getTime()

  return (
    <Block strong inset className="!my-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-semibold text-white">Привет, {user.name}!</h2>

        {isSubscriptionExpired && (
          /* Если подписка неактивна */
          <div className="flex items-center gap-2 mt-1">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <p className="text-sm text-gray-400">
              Подписка <span className="text-red-400 font-medium">неактивна</span>
            </p>
          </div>
        )}
      </div>
    </Block>
  )
}
