import { NextResponse } from "next/server"
import { validateInitData } from "@/lib/telegram"
import { redis } from "@/lib/redis"

export async function POST(req: Request) {
  const { initData } = await req.json()

  if (!initData) {
    return NextResponse.json({ error: "initData missing" }, { status: 400 })
  }

  const BOT_TOKEN = process.env.BOT_TOKEN!
  if (!BOT_TOKEN) {
    return NextResponse.json({ error: "BOT_TOKEN missing" }, { status: 500 })
  }

  const isValid = validateInitData(initData, BOT_TOKEN)

  if (!isValid) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 403 })
  }

  const params = new URLSearchParams(initData)
  const rawUser = params.get("user")

  const user = rawUser ? JSON.parse(rawUser) : null

  const session = crypto.randomUUID()
  await redis.set(`session:${session}`, JSON.stringify(user), "EX", 86400)

  return NextResponse.json({
    ok: true,
    session,
    user,
  })
}
