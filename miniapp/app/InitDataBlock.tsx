"use client"

import { useEffect, useState } from "react"
import { useUserStore } from "@/store/useUserStore"

export function InitDataBlock() {
  const initData = useUserStore((s) => s.initData)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  return <pre style={{ whiteSpace: "pre-wrap" }}>{initData || "initData пустое"}</pre>
}
