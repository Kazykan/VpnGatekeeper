"use client"

import { useState, useMemo } from "react"
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
import { getErrorMessage } from "@/lib/utils"

interface CreatePaymentResponse {
  payment_id: number
  confirmation_token: string
}

interface Tariff {
  price: number
  type: "sub" | "once"
  period: string // например "1m", "3m"
}

export function Payment() {
  // 1. Получаем тарифы из ENV (парсим JSON)
  const tariffs: Tariff[] = useMemo(() => {
    try {
      const envTariffs = process.env.NEXT_PUBLIC_TARIFFS
      return envTariffs ? JSON.parse(envTariffs) : []
    } catch (e) {
      console.error("Ошибка парсинга тарифов из ENV:", e)
      return []
    }
  }, [])

  const [isProcessing, setIsProcessing] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0) // Индекс выбранного тарифа
  const [isChecking, setIsChecking] = useState(false)
  const [showWidget, setShowWidget] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const [currentPaymentId, setCurrentPaymentId] = useState<number | null>(null)

  const [errorDialog, setErrorDialog] = useState({
    opened: false,
    message: "",
  })

  const { user, loading, error } = useUserStore()
  const fetchUser = useUserStore((s) => s.fetchUser)

  // Поллинг статуса платежа
  const verifyPayment = async (paymentId: number) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get<{ status: string }>(`/api/payments/status`, {
          params: { payment_id: paymentId },
        })

        if (response.status === "success") {
          clearInterval(interval)
          setIsChecking(false)
          if (user) await fetchUser(user.telegram_id)
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

    setTimeout(() => clearInterval(interval), 600000) // 10 минут лимит
  }

  const handlePayment = async () => {
    const selectedTariff = tariffs[selectedIndex]
    if (!user || isProcessing || !selectedTariff) return

    setIsProcessing(true)
    try {
      const data = await api.post<CreatePaymentResponse>("/api/payments/create", {
        telegram_id: user.telegram_id,
        amount: selectedTariff.price,
        type: selectedTariff.type,
        // Извлекаем число месяцев из строки "1m" или "3m"
        months: parseInt(selectedTariff.period) || 1,
        unique_payload: crypto.randomUUID(),
      })

      setCurrentPaymentId(data.payment_id)
      setToken(data.confirmation_token)
      setShowWidget(true)
    } catch (e) {
      setErrorDialog({ opened: true, message: getErrorMessage(e) })
    } finally {
      setIsProcessing(false)
    }
  }

  // Вспомогательная функция для красивого названия периода
  const getPeriodLabel = (t: Tariff) => {
    if (t.type === "sub") return "Авто"
    return t.period === "3m" ? "3 мес" : "1 мес"
  }

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

  const currentTariff = tariffs[selectedIndex]

  return (
    <div className="w-full pb-10">
      <Block strong inset className="!my-2">
        <Segmented strong>
          {tariffs.map((t, index) => (
            <SegmentedButton
              key={index}
              active={selectedIndex === index}
              onClick={() => setSelectedIndex(index)}
            >
              {getPeriodLabel(t)}
            </SegmentedButton>
          ))}
        </Segmented>
      </Block>

      <BlockTitle className="!mt-4 !mb-2 uppercase text-[11px] opacity-60">
        Вариант подписки
      </BlockTitle>

      <Card className="!m-0">
        <div className="flex flex-col items-center py-8 text-center justify-center min-h-[160px]">
          {currentTariff && (
            <>
              {currentTariff.type === "sub" && (
                <div className="bg-green-600 text-white text-[10px] px-3 py-0.5 rounded-full uppercase font-black mb-3">
                  ХИТ
                </div>
              )}
              <div className="text-7xl font-black text-primary leading-none mb-1">
                {currentTariff.price}₽
              </div>
              <div className="text-sm font-bold uppercase opacity-50">
                {currentTariff.type === "sub" ? "Ежемесячное списание" : "Разовый платеж"}
              </div>
              {currentTariff.period === "3m" && (
                <div className="text-green-500 text-xs mt-2 font-bold italic">
                  Выгодное предложение
                </div>
              )}
            </>
          )}
        </div>

        <div className="px-4 pb-4">
          <Button
            large
            rounded
            disabled={isProcessing || !currentTariff}
            onClick={handlePayment}
            className={currentTariff?.type === "sub" ? "shadow-md" : ""}
          >
            {isProcessing ? (
              <div className="flex items-center space-x-2">
                <Preloader className="w-5 h-5" />
                <span>Загрузка...</span>
              </div>
            ) : currentTariff?.type === "sub" ? (
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
        title="Уведомление"
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
