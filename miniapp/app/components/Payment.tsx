"use client"

import { useState } from "react"
import {
  Segmented,
  SegmentedButton,
  Block,
  BlockTitle,
  Button,
  Card,
  Dialog,
  DialogButton,
  Preloader,
} from "konsta/react"
import { useUserStore } from "@/store/useUserStore"
import YooKassaWidget from "./YooKassaWidget"
import { api } from "@/lib/api"

interface CreatePaymentResponse {
  payment_id: number
  confirmation_token: string
}

export function Payment() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [activeSegmented, setActiveSegmented] = useState(2)
  const [isChecking, setIsChecking] = useState(false)
  const [showWidget, setShowWidget] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const [currentPaymentId, setCurrentPaymentId] = useState<number | null>(null)

  const [errorDialog, setErrorDialog] = useState({
    opened: false,
    message: "",
  })

  const { user, loading, error, setUser } = useUserStore()

  // Функция для тихого обновления данных пользователя без перезагрузки страницы
  const refreshUserData = async () => {
    if (!user?.telegram_id) return
    try {
      const updatedUser = await api.get<any>(`/api/user/check`, {
        params: { telegram_id: user.telegram_id },
      })
      if (updatedUser) setUser(updatedUser)
    } catch (e) {
      console.error("Ошибка обновления данных пользователя:", e)
    }
  }

  // 1. Функция проверки статуса (Polling)
  const verifyPayment = async (paymentId: number) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get<{ status: string }>(`/api/payments/status`, {
          params: { payment_id: paymentId },
        })

        console.log("Статус платежа:", response.status)

        if (response.status === "success") {
          clearInterval(interval)
          setIsChecking(false)
          await refreshUserData() // Обновляем данные в Zustand
          setErrorDialog({ opened: true, message: "Оплата подтверждена! Подписка активирована." })
        } else if (response.status === "failed") {
          clearInterval(interval)
          setIsChecking(false)
          setErrorDialog({ opened: true, message: "Платеж отклонен банком." })
        }
      } catch (e) {
        console.error("Ошибка опроса статуса:", e)
      }
    }, 3000)

    // Лимит 10 минут
    setTimeout(() => clearInterval(interval), 600000)
  }

  // 2. Функция создания платежа
  const handlePayment = async () => {
    if (!user || isProcessing) return

    const tariff = {
      1: { amount: 80, type: "once", months: 1 },
      2: { amount: 70, type: "sub", months: 1 },
      3: { amount: 210, type: "once", months: 3 },
    }[activeSegmented as 1 | 2 | 3]

    if (!tariff) {
      setErrorDialog({ opened: true, message: "Тариф не найден" })
      return
    }

    setIsProcessing(true)
    try {
      const data = await api.post<CreatePaymentResponse>("/api/payments/create", {
        telegram_id: user.telegram_id,
        amount: tariff.amount,
        type: tariff.type,
        months: tariff.months,
        unique_payload: crypto.randomUUID(),
      })

      setCurrentPaymentId(data.payment_id)
      setToken(data.confirmation_token)
      setShowWidget(true)
    } catch (e: any) {
      const errorMsg = e.response?.data?.error || "Ошибка создания платежа"
      setErrorDialog({ opened: true, message: errorMsg })
    } finally {
      setIsProcessing(false)
    }
  }

  // --- РЕНДЕРЫ СОСТОЯНИЙ ---

  if (loading) return <div className="p-8 text-center text-gray-400">Загрузка...</div>
  if (error) return <div className="p-8 text-center text-red-500">Ошибка: {error}</div>
  if (!user) return <div className="p-8 text-center text-gray-400">Пользователь не авторизован</div>

  if (isChecking) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <Preloader className="mb-4 w-10 h-10" />
        <h3 className="text-lg font-bold">Ожидаем подтверждение</h3>
        <p className="text-sm opacity-60">
          Ваш платеж обрабатывается. Как только банк подтвердит операцию, доступ откроется
          автоматически.
        </p>
      </div>
    )
  }

  if (showWidget && token) {
    return (
      <div className="flex flex-col min-h-screen bg-white">
        <div className="p-2 border-b">
          <Button clear onClick={() => setShowWidget(false)}>
            ← Отмена
          </Button>
        </div>
        <div className="flex-1">
          <YooKassaWidget
            confirmationToken={token}
            onSuccess={() => {
              setShowWidget(false)
              setIsChecking(true)
              if (currentPaymentId) verifyPayment(currentPaymentId)
            }}
            onError={(err) => {
              console.error(err)
              setErrorDialog({ opened: true, message: "Ошибка во время оплаты" })
              setShowWidget(false)
            }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="w-full pb-10">
      <Block strong inset className="!my-2">
        <Segmented strong>
          {[1, 2, 3].map((val) => (
            <SegmentedButton
              key={val}
              active={activeSegmented === val}
              onClick={() => setActiveSegmented(val)}
            >
              {val === 1 ? "1 мес" : val === 2 ? "Авто" : "3 мес"}
            </SegmentedButton>
          ))}
        </Segmented>
      </Block>

      <BlockTitle className="!mt-4 !mb-2 uppercase text-[11px] opacity-60">
        Вариант подписки
      </BlockTitle>

      <Card className="!m-0">
        <div className="flex flex-col items-center py-8 text-center justify-center min-h-[160px]">
          {activeSegmented === 1 && (
            <>
              <div className="text-5xl font-bold mb-1">80₽</div>
              <div className="text-gray-400 text-sm">разовый платеж</div>
            </>
          )}

          {activeSegmented === 2 && (
            <>
              <div className="bg-green-600 text-white text-[10px] px-3 py-0.5 rounded-full uppercase font-black mb-3">
                ХИТ
              </div>
              <div className="text-7xl font-black text-primary leading-none mb-1">70₽</div>
              <div className="text-sm font-bold uppercase">Ежемесячно</div>
            </>
          )}

          {activeSegmented === 3 && (
            <>
              <div className="text-5xl font-bold mb-1">210₽</div>
              <div className="text-gray-400 text-sm italic">выгода 30₽</div>
            </>
          )}
        </div>

        <div className="px-4 pb-4">
          <Button
            large
            rounded
            disabled={isProcessing}
            onClick={handlePayment}
            className={activeSegmented === 2 ? "shadow-md" : ""}
          >
            {isProcessing ? (
              <div className="flex items-center space-x-2">
                <Preloader className="w-5 h-5" />
                <span>Загрузка...</span>
              </div>
            ) : activeSegmented === 2 ? (
              "Подписаться"
            ) : (
              "Купить"
            )}
          </Button>
        </div>
      </Card>

      <Dialog
        opened={errorDialog.opened}
        onBackdropClick={() => setErrorDialog({ opened: false, message: "" })}
        title="Упс!"
        content={errorDialog.message}
        buttons={
          <DialogButton onClick={() => setErrorDialog({ opened: false, message: "" })}>
            Закрыть
          </DialogButton>
        }
      />
    </div>
  )
}
