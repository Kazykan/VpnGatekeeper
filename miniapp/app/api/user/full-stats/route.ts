import { NextResponse } from "next/server"
import djangoApi from "@/lib/django"

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const telegram_id = searchParams.get("telegram_id")

    if (!telegram_id) {
      return NextResponse.json({ error: "Required tg_id" }, { status: 400 })
    }

    // Вызываем метод, который мы добавили в Шаге 1
    const stats = await djangoApi.getFullTrafficStats(Number(telegram_id))

    return NextResponse.json(stats)
  } catch (error: any) {
    return NextResponse.json({ error: "Failed to fetch stats" }, { status: 500 })
  }
}
