import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { redis } from "@/lib/redis"

export async function proxy(req: NextRequest) {
  const url = req.nextUrl.pathname

  // 1. Игнорируем системные файлы Next.js и запросы авторизации
  if (url.startsWith("/_next") || url.includes("/api/auth/")) {
    return NextResponse.next()
  }

  // 2. Проверяем только защищенные маршруты
  if (url.startsWith("/api/user/")) {
    const auth = req.headers.get("authorization")

    if (!auth?.startsWith("Bearer ")) {
      console.log("❌ NO BEARER TOKEN")
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const session = auth.replace("Bearer ", "").trim()
    const data = await redis.get(`session:${session}`)

    if (!data) {
      console.log("❌ INVALID SESSION:", session)
      return NextResponse.json({ error: "Invalid session" }, { status: 401 })
    }

    console.log("✅ SESSION OK:", session)
  }

  // 3. Продолжаем выполнение запроса к API роуту
  return NextResponse.next()
}

export const config = {
  // Запускаем прокси на все API, кроме auth, и на корень
  matcher: ["/api/user/:path*", "/((?!_next/static|_next/image|favicon.ico).*)"],
}
