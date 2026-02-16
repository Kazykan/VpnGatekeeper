"use client"

import React from "react"
import { Block, Button } from "konsta/react"
import { Unplug, ChevronRight } from "lucide-react"

interface Props {
  onClick: () => void
}

export function ConnectAction({ onClick }: Props) {
  return (
    <Block strong inset className="!my-2">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 p-2 rounded-lg">
            <Unplug className="text-primary" size={24} />
          </div>
          <div>
            <h3 className="font-bold">Готов к работе</h3>
            <p className="text-xs text-gray-500">Настрой подключение за 1 минуту</p>
          </div>
        </div>
      </div>

      <Button large className="flex items-center justify-center gap-2" onClick={onClick}>
        Получить настройки
        <ChevronRight size={18} />
      </Button>
    </Block>
  )
}
