import { NextResponse } from "next/server"
import djangoApi from "@/lib/django"

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const userId = searchParams.get("user")

  if (!userId) {
    return NextResponse.json({ error: "user param required" }, { status: 400 })
  }

  try {
    const data = await djangoApi.getCredentialsByUser(Number(userId))
    return NextResponse.json(data)
  } catch (e: any) {
    return NextResponse.json(
      { error: e.response?.data || "Internal error" },
      { status: e.response?.status || 500 },
    )
  }
}
