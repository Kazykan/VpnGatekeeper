"use client"

import { useState, useMemo } from "react"
import {
  Segmented,
  SegmentedButton,
  Block,
  BlockTitle,
  Button,
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
  period: string
}

export function Payment() {
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
  const [selectedIndex, setSelectedIndex] = useState(0)
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
          setErrorDialog({ opened: true, message: "Доступ успешно активирован." })
        } else if (response.status === "failed") {
          clearInterval(interval)
          setIsChecking(false)
          setErrorDialog({ opened: true, message: "Ошибка транзакции." })
        }
      } catch (e) {
        console.error("Ошибка опроса статуса:", e)
      }
    }, 3000)
    setTimeout(() => clearInterval(interval), 600000)
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

  const getPeriodLabel = (t: Tariff) => {
    if (t.type === "sub") return "Авто"
    return t.period === "3m" ? "90 дней" : "30 дней"
  }

  if (loading) return <div className="p-8 text-center text-gray-400 font-sans">Загрузка...</div>
  if (error) return <div className="p-8 text-center text-red-500 font-sans">{error}</div>
  if (!user) return <div className="p-8 text-center text-gray-400 font-sans">Не авторизован</div>

  if (isChecking) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center font-sans">
        <Preloader className="mb-4 w-10 h-10" />
        <h3 className="text-lg font-bold">Ожидание активации</h3>
        <p className="text-sm opacity-60">Проверяем статус платежа...</p>
      </div>
    )
  }

  if (showWidget && token) {
    return (
      <div className="flex flex-col min-h-screen bg-white font-sans">
        <div className="p-2 border-b">
          <Button clear onClick={() => setShowWidget(false)}>
            ← Назад
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
              setErrorDialog({ opened: true, message: "Ошибка оплаты" })
              setShowWidget(false)
            }}
          />
        </div>
      </div>
    )
  }

  const currentTariff = tariffs[selectedIndex]

  return (
    <div className="w-full pb-8 font-sans">
      <BlockTitle className="mt-6! mb-2! uppercase text-2xs tracking-widest opacity-50 px-4">
        Параметры услуги
      </BlockTitle>

      {/* ГЛАВНОЕ ИЗМЕНЕНИЕ: Всё внутри одного Block strong inset */}
      <Block strong inset className="my-0! space-y-6 pt-4 pb-6">
        {/* Переключатель тарифов */}
        <Segmented strong rounded className="border-2 border-primary/10">
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

        {/* Блок цены (теперь без фона, чтобы не было квадратов) */}
        <div className="flex flex-col items-center py-2 text-center">
          {currentTariff && (
            <>
              {/* Этот блок теперь ПРИСУТСТВУЕТ всегда, поэтому высота не меняется */}
              <div
                className="text-primary text-[9px] font-bold uppercase tracking-tighter mb-2 transition-opacity duration-200"
                style={{
                  opacity: currentTariff.type === "sub" ? 1 : 0,
                  visibility: currentTariff.type === "sub" ? "visible" : "hidden",
                }}
              >
                ● Оптимальный выбор
              </div>

              <div className="flex items-baseline justify-center">
                <span className="text-6xl font-black text-primary tracking-tighter leading-none">
                  {currentTariff.price}₽
                </span>
                <span className="ml-1 text-sm font-bold opacity-30">
                  /{currentTariff.period === "3m" ? "3мес" : "мес"}
                </span>
              </div>

              {/* 3. Текст про автопродление */}
              <div
                className="mt-2 min-h-3.5 text-2xs font-medium transition-opacity duration-200"
                style={{
                  opacity: currentTariff.type === "sub" ? 1 : 0,
                  color: "#f97316", // Оранжевый (orange-500) напрямую для надежности
                }}
              >
                Автоматическое продление каждые 30 дней
              </div>

              {/* 4. Невидимый блок-заглушка для разового платежа (чтобы высота не прыгала) */}
              <div
                className="text-2xs font-medium text-gray-400"
                style={{
                  display: currentTariff.type === "once" ? "block" : "none",
                }}
              >
                Разовый платеж
              </div>
            </>
          )}
        </div>

        {/* Описание услуги мелким шрифтом */}
        <div className="text-center px-2">
          <p className="text-[12px] leading-snug text-gray-500 italic opacity-80">
            Персональное проксирование данных для защиты трафика и безопасного доступа к сетевым
            ресурсам (IT-услуга).
          </p>
        </div>

        {/* Кнопка действия */}
        <div className="px-2">
          <Button
            large
            rounded
            disabled={isProcessing || !currentTariff}
            onClick={handlePayment}
            className="shadow-sm"
          >
            {isProcessing ? (
              <div className="flex items-center space-x-2">
                <Preloader className="w-4 h-4" />
                <span>Загрузка...</span>
              </div>
            ) : (
              "Оформить доступ"
            )}
          </Button>
        </div>

        {/* Нижние метки для солидности */}
        <div className="flex justify-center space-x-6 opacity-20 text-[8px] font-bold uppercase tracking-widest pt-2">
          <span>TLS Encryption</span>
          <span>Dedicated Port</span>
        </div>
      </Block>

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
