import { NextResponse } from "next/server"
import djangoApi from "@/lib/django"

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const telegram_id = searchParams.get("telegram_id") // Важно: проверь, tg_id или telegram_id в Django
    console.log(" [API] Запрос для TG_ID:", telegram_id)

    if (!telegram_id) {
      return NextResponse.json({ error: "telegram_id is required" }, { status: 400 })
    }

    // Вызываем метод Django API
    const data = await djangoApi.getCredentialConfigByTg(telegram_id)

    return NextResponse.json(data)
  } catch (error: any) {
    console.error("Error in /api/credentials/config-by-tg:", error)

    return NextResponse.json(
      { error: error.response?.data || "Internal Server Error" },
      { status: error.response?.status || 500 },
    )
  }
}
