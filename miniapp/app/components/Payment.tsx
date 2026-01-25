"use client"

import React, { useState } from "react"
import {
  Segmented,
  SegmentedButton,
  Block,
  BlockTitle,
  Button,
  Card,
  Dialog,
  DialogButton,
} from "konsta/react"
import { useUserStore } from "@/store/useUserStore"
import { DjangoAPI } from "@/lib/django"
import YooKassaWidget from "./YooKassaWidget"

export function Payment() {
  const [activeSegmented, setActiveSegmented] = useState(2)

  // 👉 состояния для виджета
  const [showWidget, setShowWidget] = useState(false)
  const [token, setToken] = useState<string | null>(null)

  // 👉 состояние для Konsta UI Alert
  const [errorDialog, setErrorDialog] = useState({
    opened: false,
    message: "",
  })

  const { user, loading, error } = useUserStore()

  // 👉 безопасная загрузка
  if (loading) {
    return <div className="p-4 text-center text-gray-400">Загрузка…</div>
  }
  if (error) {
    return <div className="p-4 text-center text-red-500">Ошибка: {error}</div>
  }
  if (!user) {
    return <div className="p-4 text-center text-gray-400">Пользователь не найден</div>
  }

  const handlePayment = async () => {
    const tariff = {
      1: { amount: 80, type: "once", months: 1 },
      2: { amount: 70, type: "sub", months: 1 },
      3: { amount: 210, type: "once", months: 3 },
    }[activeSegmented]

    if (!tariff) {
      setErrorDialog({ opened: true, message: "Ошибка: тариф не найден" })
      return
    }

    const djangoApi = new DjangoAPI()

    try {
      const resp = await djangoApi.createPayment({
        telegram_id: user.telegram_id,
        amount: tariff.amount,
        type: tariff.type,
        months: tariff.months,
        unique_payload: crypto.randomUUID(),
      })

      if (!resp.confirmation_token) {
        setErrorDialog({
          opened: true,
          message: "Ошибка: Django не вернул confirmation_token",
        })
        return
      }

      // 👉 показываем виджет
      setToken(resp.confirmation_token)
      setShowWidget(true)
    } catch (e) {
      console.error(e, JSON.stringify(e))
      setErrorDialog({
        opened: true,
        message: `Ошибка при создании платежа ${JSON.stringify(e)}`,
      })
    }
  }

  // 👉 если виджет активен — показываем только его
  if (showWidget && token) {
    return (
      <>
        <div className="mt-4">
          <YooKassaWidget
            confirmationToken={token}
            onSuccess={() => {
              setShowWidget(false)
            }}
            onError={(err) => {
              console.error(err)
              setErrorDialog({
                opened: true,
                message: "Ошибка оплаты",
              })
              setShowWidget(false)
            }}
          />
        </div>

        {/* Диалог ошибок */}
        <Dialog
          opened={errorDialog.opened}
          onBackdropClick={() => setErrorDialog({ opened: false, message: "" })}
          title="Ошибка"
          content={errorDialog.message}
          buttons={
            <DialogButton strong onClick={() => setErrorDialog({ opened: false, message: "" })}>
              OK
            </DialogButton>
          }
        />
      </>
    )
  }

  // 👉 обычный UI тарифов
  return (
    <>
      <div className="w-full overflow-hidden">
        <Block strong inset className="!my-2">
          <Segmented strong>
            <SegmentedButton active={activeSegmented === 1} onClick={() => setActiveSegmented(1)}>
              1 мес
            </SegmentedButton>
            <SegmentedButton active={activeSegmented === 2} onClick={() => setActiveSegmented(2)}>
              Авто
            </SegmentedButton>
            <SegmentedButton active={activeSegmented === 3} onClick={() => setActiveSegmented(3)}>
              3 мес
            </SegmentedButton>
          </Segmented>
        </Block>

        <BlockTitle className="!mt-4 !mb-2 uppercase text-[11px] opacity-60">
          Выбранный тариф
        </BlockTitle>

        <Card strong inset className="!m-0">
          <div className="flex flex-col items-center py-6 text-center min-h-[140px] justify-center">
            {activeSegmented === 1 && (
              <>
                <div className="text-4xl font-bold mb-1">80₽</div>
                <div className="text-gray-400 text-sm italic">разовая оплата</div>
              </>
            )}

            {activeSegmented === 2 && (
              <>
                <div className="bg-green-600 text-white text-[10px] px-2 py-0.5 rounded-full uppercase font-bold mb-2 tracking-wide">
                  Выгодно
                </div>
                <div className="text-6xl font-black text-primary leading-none mb-2">70₽</div>
                <div className="text-sm font-bold text-primary uppercase tracking-tight">
                  Автосписание
                </div>
                <div className="text-[11px] opacity-50 mt-1 italic">70₽ каждый месяц</div>
              </>
            )}

            {activeSegmented === 3 && (
              <>
                <div className="text-4xl font-bold mb-1">210₽</div>
                <div className="text-gray-400 text-sm">за 3 месяца</div>
                <div className="text-[11px] opacity-50 mt-1 uppercase font-semibold">
                  Экономия 30₽
                </div>
              </>
            )}
          </div>

          <div className="mt-4">
            <Button
              large
              rounded
              onClick={handlePayment}
              className={
                activeSegmented === 2
                  ? "shadow-lg scale-[1.02] active:scale-95 transition-transform"
                  : ""
              }
            >
              {activeSegmented === 2 ? "Подписаться за 70₽" : "Оплатить"}
            </Button>
          </div>
        </Card>

        <div className="px-4 mt-3 mb-2 text-center">
          <p className="text-[10px] text-gray-500 leading-tight opacity-40 uppercase">
            Отмена подписки доступна в любой момент в боте
          </p>
        </div>
      </div>

      {/* Диалог ошибок */}
      <Dialog
        opened={errorDialog.opened}
        onBackdropClick={() => setErrorDialog({ opened: false, message: "" })}
        title="Ошибка"
        content={errorDialog.message}
        buttons={
          <DialogButton strong onClick={() => setErrorDialog({ opened: false, message: "" })}>
            OK
          </DialogButton>
        }
      />
    </>
  )
}
