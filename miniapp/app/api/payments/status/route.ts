import { NextResponse } from "next/server"
import djangoApi from "@/lib/django"

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const paymentId = searchParams.get("payment_id")

    if (!paymentId) {
      return NextResponse.json({ error: "payment_id is required" }, { status: 400 })
    }

    const payment = await djangoApi.getPaymentStatus(Number(paymentId))

    if (!payment) {
      return NextResponse.json({ error: "Payment not found" }, { status: 404 })
    }

    // Возвращаем только статус, чтобы фронтенд знал, что делать
    return NextResponse.json({ status: payment.status })
  } catch (error: any) {
    console.error("Status Check Error:", error.response?.data || error.message)
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
  }
}
