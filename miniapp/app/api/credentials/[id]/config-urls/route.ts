import { NextResponse } from "next/server"
import djangoApi from "@/lib/django"

export async function GET(req: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params
    const credentialId = Number(id)

    if (isNaN(credentialId)) {
      return NextResponse.json({ error: "Invalid credential ID" }, { status: 400 })
    }

    const data = await djangoApi.getCredentialConfigUrls(credentialId)

    // Гарантируем сериализацию
    return NextResponse.json({ ...data })
  } catch (error: any) {
    console.error("Error in /api/credentials/[id]/config-urls:", error)

    return NextResponse.json(
      { error: error.response?.data || "Internal Server Error" },
      { status: error.response?.status || 500 },
    )
  }
}
