import { NextResponse } from "next/server"
import { DjangoAPI } from "@/lib/django"

export async function POST(req: Request) {
  try {
    const body = await req.json()
    console.log("1. Отправляем в Django:", body)

    const api = new DjangoAPI()
    const paymentData = await api.createPayment(body)

    console.log("2. Django ответил:", paymentData) // Должно быть { payment_id, confirmation_token }

    return NextResponse.json(paymentData)
  } catch (error: any) {
    // Важно: выводим ошибку из axios (error.response.data)
    console.error("Django Error Details:", error.response?.data || error.message)
    return NextResponse.json(
      { error: error.response?.data || "Internal Server Error" },
      { status: error.response?.status || 500 }
    )
  }
}
