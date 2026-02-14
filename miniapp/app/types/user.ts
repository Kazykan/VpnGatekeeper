export interface User {
  id: number
  name: string
  sub_token: string      // <-- ОБЯЗАТЕЛЬНО для ссылки подписки
  telegram_id: number
  xray_id?: string | null
  end_date?: string | null
  invited_by?: number | null
  traffic_on: boolean
  autopay_enabled: boolean
  payment_method_id?: string | null
}