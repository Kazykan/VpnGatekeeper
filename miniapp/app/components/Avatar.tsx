"use client"

import { User } from "@/store/useUserStore"
import { useEffect, useState } from "react"
import { useSessionStore } from "@/store/useSessionStore"

interface AvatarProps {
  user: User
  size?: number
}

export function Avatar({ user, size = 44 }: AvatarProps) {
  const [photo, setPhoto] = useState<string | null>(null)
  const session = useSessionStore((s) => s.session)

  useEffect(() => {
    // Важно: не делаем запрос, если нет сессии или она пустая
    if (!user?.id || !session || session === "undefined") return

    let isMounted = true

    fetch(`/api/user/photo?user_id=${user.id}`, {
      headers: {
        Authorization: `Bearer ${session}`,
      },
    })
      .then(async (r) => {
        if (!r.ok) throw new Error("Photo not found")
        // Читаем ответ как Blob (бинарные данные картинки)
        const blob = await r.blob()
        return URL.createObjectURL(blob)
      })
      .then((url) => {
        if (isMounted) setPhoto(url)
      })
      .catch(() => {
        if (isMounted) setPhoto(null)
      })

    return () => {
      isMounted = false
      if (photo) URL.revokeObjectURL(photo) // Очистка памяти
    }
  }, [user.id, session])

  const initials = (user.first_name?.[0] || "") + (user.last_name?.[0] || "")

  return (
    <div
      className="rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xl font-medium overflow-hidden shrink-0"
      style={{ width: size, height: size }}
    >
      {photo ? (
        <img src={photo} alt="avatar" className="w-full h-full object-cover" />
      ) : (
        <span>{initials || "?"}</span>
      )}
    </div>
  )
}
