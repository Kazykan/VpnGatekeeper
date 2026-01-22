interface TelegramWebApp {
  initData: string
  initDataUnsafe: any
  ready: () => void
  expand: () => void
  openTelegramLink: (url: string) => void
  close(): void
  disableVerticalSwipe: () => void
  themeParams: any
  BackButton: {
    show: () => void
    hide: () => void
    onClick: (cb: () => void) => void
  }
  MainButton: {
    show: () => void
    hide: () => void
    setText: (text: string) => void
    onClick: (cb: () => void) => void
  }
  HapticFeedback: {
    impactOccurred: (style: string) => void
  }
}

interface Window {
  Telegram: {
    WebApp: TelegramWebApp
  }
}
