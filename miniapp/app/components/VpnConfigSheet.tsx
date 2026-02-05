"use client"

import { Sheet, Block, Button, List, ListItem } from "konsta/react"

export function VpnConfigSheet({
  opened,
  onClose,
  config,
}: {
  opened: boolean
  onClose: () => void
  config: any | null
}) {
  return (
    <Sheet opened={opened} onBackdropClick={onClose} className="pb-safe">
      <Block strong className="text-center">
        <h2 className="font-bold text-lg mb-2">Ваш VPN конфиг</h2>
        <p className="text-gray-500 text-sm">Скопируйте нужный формат</p>
      </Block>

      {config ? (
        <List strong inset>
          <ListItem
            title="Amnezia URL"
            after={
              <Button small onClick={() => navigator.clipboard.writeText(config.amnezia_url)}>
                Копировать
              </Button>
            }
            text={config.amnezia_url}
          />

          <ListItem
            title="iOS VPN URL"
            after={
              <Button small onClick={() => navigator.clipboard.writeText(config.default_vpn_url)}>
                Копировать
              </Button>
            }
            text={config.default_vpn_url}
          />

          <ListItem
            title="VLESS"
            after={
              <Button small onClick={() => navigator.clipboard.writeText(config.vless_raw)}>
                Копировать
              </Button>
            }
            text={config.vless_raw}
          />

          <ListItem
            title="WireGuard"
            after={
              <Button small onClick={() => navigator.clipboard.writeText(config.raw_wg_conf)}>
                Копировать
              </Button>
            }
            text="Открыть конфиг"
            onClick={() => {
              const blob = new Blob([config.raw_wg_conf], { type: "text/plain" })
              const url = URL.createObjectURL(blob)
              window.open(url, "_blank")
            }}
          />
        </List>
      ) : (
        <Block strong inset className="text-center text-gray-500">
          Загрузка...
        </Block>
      )}

      <Block strong inset>
        <Button large onClick={onClose}>
          Закрыть
        </Button>
      </Block>
    </Sheet>
  )
}
