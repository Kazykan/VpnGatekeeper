import { NextResponse } from "next/server"
import { redis } from "@/lib/redis"
import djangoApi from "@/lib/django"

export async function GET(req: Request) {
  // 1. Извлекаем token из query параметров (?token=...)
  const { searchParams } = new URL(req.url)
  const token = searchParams.get("token")

  if (!token) {
    return NextResponse.json({ error: "Token missing" }, { status: 400 })
  }

  try {
    // 2. Запрашиваем данные из Django
    const users = await djangoApi.getUserBySubToken(token)

    // Создаем UUID сессии (даже если юзер не найден, как в твоем примере)
    const session = crypto.randomUUID()

    // 3. ПРОВЕРКА: Если пользователь найден (массив не пустой)
    if (Array.isArray(users) && users.length > 0) {
      const django_first_user = users[0]

      // Записываем данные в Redis для сессии
      const sessionData = {
        id: django_first_user.telegram_id,
        name: django_first_user.name,
        is_external: true,
      }
      await redis.set(`session:${session}`, JSON.stringify(sessionData), "EX", 86400)

      // Возвращаем строго в том же формате, что и Auth Telegram
      return NextResponse.json({
        ok: true,
        session,
        django_first_user,
      })
    }

    // 4. Если пользователя нет — возвращаем структуру с null
    return NextResponse.json({
      ok: false,
      session,
      django_first_user: null,
    })
  } catch (error: any) {
    console.error("[AuthByToken] Error:", error.message)
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
  }
}
