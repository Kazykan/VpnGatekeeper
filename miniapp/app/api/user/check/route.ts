import { NextResponse } from "next/server"
import djangoApi from "@/lib/django"

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const telegram_id = searchParams.get("telegram_id")

    if (!telegram_id) {
      return NextResponse.json({ error: "telegram_id is required" }, { status: 400 })
    }

    const users = await djangoApi.getUsersByTelegramId(Number(telegram_id))

    if (Array.isArray(users) && users.length > 0) {
      return NextResponse.json(users[0])
    }

    return NextResponse.json(null)
  } catch (error: any) {
    console.error("Error in /api/user/check:", error.response?.data || error.message)

    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
