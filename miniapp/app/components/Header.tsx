"use client"

import { Navbar, NavbarBackLink } from "konsta/react"
import Image from "next/image"
import { Avatar } from "./Avatar" // Предполагаю, он там
import { User } from "../types/user";

interface HeaderProps {
  user: User | null; // Добавил | null, так как на старте юзера может не быть
  session: string | null; // Заменили any на реальный тип из стора
}

export function Header({ user, session }: HeaderProps) {
  return (
    <Navbar
      // Логотип и название слева
      title={
        <div className="flex items-center gap-2">
          <Image
            src="/Rufat_logo.png"
            alt="Logo"
            width={45}
            height={45}
            className="rounded-lg shadow-sm"
          />
          <span className="font-bold text-[17px] tracking-tight">Rufat Connect</span>
        </div>
      }
      // Аватар справа
      right={user && session && <Avatar user={user} />}
      className="top-0 sticky"
    />
  )
}
