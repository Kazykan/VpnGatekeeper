import { NextResponse } from "next/server"
import { DjangoAPI } from "@/lib/django"

export async function POST(req: Request) {
  try {
    const body = await req.json()

    // Вызываем Django API на стороне сервера
    const api = new DjangoAPI()
    const paymentData = await api.createPayment(body)

    return NextResponse.json(paymentData)
  } catch (error: any) {
    console.error("Payment API Error:", error.message)
    return NextResponse.json({ error: error.message || "Internal Server Error" }, { status: 500 })
  }
}
