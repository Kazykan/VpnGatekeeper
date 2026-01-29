import axios, { AxiosInstance } from "axios"

// Создаем внутренний экземпляр
const instance = axios.create({
  baseURL: "/",
  headers: {
    "Content-Type": "application/json",
  },
})

// Интерцепторы (те же самые)
instance.interceptors.request.use((config) => {
  const session = typeof window !== "undefined" ? localStorage.getItem("session") : null
  if (session && config.headers) {
    config.headers.Authorization = `Bearer ${session}`
  }
  return config
})

instance.interceptors.response.use(
  (response) => response.data, // РАСПАКОВКА
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("session")
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

// ГЛАВНОЕ: Экспортируем с "обманкой" для TypeScript
// Мы говорим, что методы возвращают Promise<T>, а не Promise<AxiosResponse<T>>
export const api = instance as unknown as {
  get<T = any>(url: string, config?: any): Promise<T>
  post<T = any>(url: string, data?: any, config?: any): Promise<T>
  put<T = any>(url: string, data?: any, config?: any): Promise<T>
  patch<T = any>(url: string, data?: any, config?: any): Promise<T>
  delete<T = any>(url: string, config?: any): Promise<T>
}
