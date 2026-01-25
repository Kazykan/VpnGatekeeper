"use client"

import { Navbar, NavbarBackLink } from "konsta/react"
import Image from "next/image"
import { Avatar } from "./Avatar" // Предполагаю, он там

export function Header({ user, session }: { user: any; session: any }) {
  return (
    <Navbar
      // Логотип и название слева
      title={
        <div className="flex items-center gap-2">
          <Image
            src="/Rufat_logo.png"
            alt="Logo"
            width={28}
            height={28}
            className="rounded-lg shadow-sm"
          />
          <span className="font-bold text-[17px] tracking-tight">Rufat VPN</span>
        </div>
      }
      // Аватар справа
      right={user && session && <Avatar user={user} />}
      className="top-0 sticky"
    />
  )
}
