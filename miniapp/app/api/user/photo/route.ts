import { NextResponse } from "next/server"

const BOT_TOKEN = process.env.BOT_TOKEN!
const CACHE = new Map<string, string>() // user_id -> file_path

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const userId = searchParams.get("user_id")

  if (!userId) {
    return NextResponse.json({ error: "user_id missing" }, { status: 400 })
  }

  // 1. Проверяем кэш file_path
  let filePath = CACHE.get(userId)

  if (!filePath) {
    // 2. Получаем file_id
    const photos = await fetch(
      `https://api.telegram.org/bot${BOT_TOKEN}/getUserProfilePhotos?user_id=${userId}&limit=1`
    ).then((r) => r.json())

    if (!photos?.result?.photos?.length) {
      return NextResponse.json({ error: "no_photo" }, { status: 404 })
    }

    const fileId = photos.result.photos[0].at(-1).file_id

    // 3. Получаем file_path
    const file = await fetch(
      `https://api.telegram.org/bot${BOT_TOKEN}/getFile?file_id=${fileId}`
    ).then((r) => r.json())

    filePath = file?.result?.file_path
    if (!filePath) {
      return NextResponse.json({ error: "file_not_found" }, { status: 404 })
    }

    CACHE.set(userId, filePath)
  }

  // 4. Скачиваем файл с Telegram CDN
  const fileUrl = `https://api.telegram.org/file/bot${BOT_TOKEN}/${filePath}`
  const fileResp = await fetch(fileUrl)

  if (!fileResp.ok) {
    return NextResponse.json({ error: "download_failed" }, { status: 500 })
  }

  const buffer = Buffer.from(await fileResp.arrayBuffer())

  // 5. Отдаём файл напрямую клиенту
  return new NextResponse(buffer, {
    headers: {
      "Content-Type": fileResp.headers.get("Content-Type") || "image/jpeg",
      "Cache-Control": "public, max-age=86400",
    },
  })
}
