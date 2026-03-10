// app/api/payments/unbind-card/route.ts
import { NextResponse } from "next/server"
import djangoApi from "@/lib/django"

export async function POST(req: Request) {
  try {
    const { telegram_id } = await req.json()

    if (!telegram_id) {
      return NextResponse.json({ error: "telegram_id is required" }, { status: 400 })
    }

    // Вызываем метод в lib/django.ts (его мы добавим следующим шагом)
    const result = await djangoApi.unbindCard(telegram_id)

    return NextResponse.json(result)
  } catch (error: any) {
    console.error("Unbind Error:", error.response?.data || error.message)
    return NextResponse.json(
      { error: error.response?.data?.error || "Internal Server Error" },
      { status: error.response?.status || 500 },
    )
  }
}
