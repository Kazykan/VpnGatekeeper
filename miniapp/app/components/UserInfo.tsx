"use client"

import { Block, List, ListItem } from "konsta/react"

export function UserInfo({ user }: { user: any }) {
  return (
    <Block strong inset className="!my-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-semibold text-white">Привет, {user.name}!</h2>
        <div className="flex items-center gap-2 mt-1">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <p className="text-sm text-gray-400">
            Подписка активна до: <span className="text-white font-medium">{user.end_date}</span>
          </p>
        </div>
      </div>
    </Block>
  )
}
