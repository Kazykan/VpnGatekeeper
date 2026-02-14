import axios from "axios"

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.error || error.message
  }
  return error instanceof Error ? error.message : String(error)
}
