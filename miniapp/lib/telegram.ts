import crypto from "crypto"

// Публичные ключи Telegram (официальные)
const TELEGRAM_PUBLIC_KEY_PROD = "e7bf03a2fa4602af4580703d88dda5bb59f32ed8b02a56c187fe7d34caed242d"

const TELEGRAM_PUBLIC_KEY_TEST = "40055058a4ee38156a06562e52eece92a771bcd8346a8c4615cb7376eddf72ec"

// Определяем окружение (production/test)
const TELEGRAM_PUBLIC_KEY = TELEGRAM_PUBLIC_KEY_PROD

/**
 * Универсальная проверка initData:
 * - если есть hash → старый режим (HMAC-SHA256)
 * - если есть signature → новый режим (Ed25519)
 */
export function validateInitData(initData: string, botToken: string): boolean {
  const params = new URLSearchParams(initData)

  const hash = params.get("hash")
  const signature = params.get("signature")

  // -----------------------------
  // 1) Старый режим (через hash)
  // -----------------------------
  if (hash) {
    const paramsCopy = new URLSearchParams(initData)
    paramsCopy.delete("hash")

    const dataCheckString = Array.from(paramsCopy.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v}`)
      .join("\n")

    const secretKey = crypto.createHmac("sha256", "WebAppData").update(botToken).digest()

    const computedHash = crypto
      .createHmac("sha256", secretKey)
      .update(dataCheckString)
      .digest("hex")

    return computedHash === hash
  }

  // -----------------------------
  // 2) Новый режим (через signature)
  // -----------------------------
  if (signature) {
    const paramsCopy = new URLSearchParams(initData)
    paramsCopy.delete("hash")
    paramsCopy.delete("signature")

    const sorted = Array.from(paramsCopy.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v}`)
      .join("\n")

    const botId = botToken.split(":")[0]

    const dataCheckString = `${botId}:WebAppData\n${sorted}`

    // Исправляем base64 (Telegram иногда присылает без padding)
    const paddedSignature = signature + "=".repeat((4 - (signature.length % 4)) % 4)

    const signatureBytes = Buffer.from(paddedSignature, "base64")
    const publicKeyBytes = Buffer.from(TELEGRAM_PUBLIC_KEY, "hex")

    return crypto.verify(
      null,
      Buffer.from(dataCheckString),
      {
        key: Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), publicKeyBytes]),
        format: "der",
        type: "spki",
      },
      signatureBytes
    )
  }

  return false
}
