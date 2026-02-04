import { Block, BlockTitle, Icon } from "konsta/react"

interface ConnectResponse {
  amnezia_url: string
  default_vpn_url: string
  raw_conf: string
  xray: string
}

// Компонент внутри Home.js
export function Connect() {
  return (
    <Block strong inset className="space-y-4">
      <BlockTitle className="text-center">Подключение</BlockTitle>

      <div className="grid grid-cols-1 gap-3">
        {/* Кнопка для iPhone */}
        <a
          href="fdssdfsdf"
          className="flex items-center justify-between p-4 bg-white/10 rounded-xl active:scale-95 transition-transform"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">🍎</span>
            <div>
              <p className="font-bold">iOS (iPhone)</p>
              <p className="text-[10px] opacity-50">Открыть в DefaultVPN</p>
            </div>
          </div>
          <Icon material="chevron_right" />
        </a>

        {/* Кнопка для Android */}
        <a
          href="fdssdfsdfsdf"
          className="flex items-center justify-between p-4 bg-white/10 rounded-xl active:scale-95 transition-transform"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">🤖</span>
            <div>
              <p className="font-bold">Android / PC</p>
              <p className="text-[10px] opacity-50">Открыть в AmneziaVPN</p>
            </div>
          </div>
          <Icon material="chevron_right" />
        </a>
      </div>

      <div className="mt-4 p-3 bg-primary/10 rounded-lg">
        <p className="text-[11px] text-center text-primary uppercase font-bold">
          Инструкция: Нажми на кнопку выше -`{">"}` Разрешить -`{">"}` Подключить
        </p>
      </div>
    </Block>
  )
}
