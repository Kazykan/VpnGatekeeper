import { NextResponse } from "next/server"
import { DjangoAPI } from "@/lib/django"

export async function POST(req: Request) {
  try {
    const { telegram_id } = await req.json()

    if (!telegram_id) {
      return NextResponse.json({ error: "telegram_id is required" }, { status: 400 })
    }

    const api = new DjangoAPI()
    const users = await api.getUsersByTelegramId(telegram_id)

    // Если пользователь найден → вернуть его
    if (Array.isArray(users) && users.length > 0) {
      return NextResponse.json(users[0])
    }

    // Если нет → вернуть null
    return NextResponse.json(null)
  } catch (error: any) {
    console.error("Error in /api/user/check:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
