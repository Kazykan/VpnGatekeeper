"use client"
import { Block, Button } from "konsta/react"
import { useUserStore } from "@/store/useUserStore"
import { motion } from "framer-motion"

export function TrafficStats() {
  const { traffic, user, fetchTraffic } = useUserStore()

  if (!traffic || !user) return null

  // Расчет дней до конца подписки
  const daysLeft = user.end_date
    ? Math.max(
        0,
        Math.ceil((new Date(user.end_date).getTime() - new Date().getTime()) / (1000 * 3600 * 24)),
      )
    : 0

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Block strong inset className="!my-4 space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">
            Статистика трафика
          </span>
          <Button clear small className="!p-0 !w-auto h-auto" onClick={() => fetchTraffic()}>
            <span className="text-[10px] text-primary underline">обновить</span>
          </Button>
        </div>

        <div className="space-y-1">
          <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-1000 ease-out"
              style={{ width: `${traffic.percent}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] font-mono text-gray-400">
            <span>{traffic.usedGb} GB</span>
            <span>{traffic.totalGb} GB</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 border-t border-gray-100 dark:border-gray-800 pt-3">
          <div>
            <p className="text-[10px] text-gray-400 uppercase">Осталось времени</p>
            <p className="text-sm font-bold">{daysLeft} дн.</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-gray-400 uppercase">Узел связи</p>
            <p className="text-sm font-bold text-green-500 flex items-center justify-end gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              ONLINE
            </p>
          </div>
        </div>
      </Block>
    </motion.div>
  )
}
