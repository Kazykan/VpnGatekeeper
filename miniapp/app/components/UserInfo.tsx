"use client"

import { Block } from "konsta/react"
import { User } from "../types/user"

export function UserInfo({ user }: { user: User }) {
  const hasDate = Boolean(user.end_date)
  const endDate = hasDate ? new Date(user.end_date!) : null
  const now = new Date()
  const isSubscriptionExpired = !endDate || endDate.getTime() < now.getTime()

  return (
    // ИЗМЕНЕНО: !mb-2 вместо !my-4, чтобы сократить расстояние до следующего блока
    <Block strong inset className="!mt-4 !mb-2">
      <div className="flex flex-col gap-0.5 font-sans">
        <h2 className="text-xl font-bold text-white tracking-tight">Привет, {user.name}!</h2>
        {isSubscriptionExpired && (
          <div className="flex items-center gap-2 mt-1 opacity-80">
            <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            <p className="text-[12px] text-gray-400 uppercase font-semibold">
              Доступ <span className="text-red-400">приостановлен</span>
            </p>
          </div>
        )}
      </div>
    </Block>
  )
}
