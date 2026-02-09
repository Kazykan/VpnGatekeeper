import { NextResponse } from "next/server"
import djangoApi from "@/lib/django"

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const telegram_id = searchParams.get("telegram_id")

    if (!telegram_id) {
      return NextResponse.json({ error: "telegram_id is required" }, { status: 400 })
    }

    const data = await djangoApi.getCredentialConfigByTg(telegram_id)

    // 200 — новые конфиги
    if (Array.isArray(data) && data.length > 0) {
      return NextResponse.json(data, { status: 200 })
    }

    // 204 — есть только старые конфиги
    return new Response(null, { status: 204 })
  } catch (error: any) {
    const status = error.response?.status

    if (status === 404) {
      // пользователя нет
      return new Response(null, { status: 404 })
    }

    if (status === 401) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
  }
}