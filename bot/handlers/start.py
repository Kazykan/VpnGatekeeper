from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from keyboards.menu_kb import miniapp_keyboard
from utils.api import register_user, user_exists

router = Router()


def register_start_handlers(dp):
    dp.include_router(router)


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user = message.from_user
    tg_id = user.id
    name = user.username or user.full_name
    args = command.args  # Параметры после ?start=

    # 1. Сначала проверяем, есть ли пользователь в базе
    is_registered = await user_exists(tg_id=tg_id)

    # 2. Обработка аргументов (если они есть)
    if args:
        # --- СЦЕНАРИЙ А: Оплата из Mini App ---
        if args.startswith("pay_"):
            # Разбираем строку типа "pay_80_once"
            try:
                parts = args.split("_")
                amount = int(parts[1])
                pay_type = parts[2]  # "once" или "sub"

                # Если по какой-то причине юзера нет в БД, регистрируем без реферала
                if not is_registered:
                    await register_user(tg_id=tg_id, name=name, invited_by=None)

                await message.answer(
                    f"💳 Вы выбрали тариф: {amount}₽ ({'подписка' if pay_type == 'sub' else 'разово'})"
                )
                # Здесь вызывай свою функцию оплаты:
                # await send_my_payment_invoice(message, amount, pay_type)
                return
            except (IndexError, ValueError):
                await message.answer("Ошибка в параметрах оплаты.")

        # --- СЦЕНАРИЙ Б: Реферальная ссылка ---
        # Извлекаем ID, убирая префикс
        ref_str = args.replace("inv_", "")

        # Переменная для итогового ID (изначально None)
        referrer_id: int | None = None

        # Проверяем, что в строке только цифры, и конвертируем в int
        if ref_str.isdigit():
            referrer_id = int(ref_str)

        # Защита от саморефералов
        if referrer_id == tg_id:
            referrer_id = None

        if not is_registered:
            # Теперь referrer_id имеет тип int | None, ошибка исчезнет
            await register_user(tg_id=tg_id, name=name, invited_by=referrer_id)
            await message.answer("🎉 Вы успешно зарегистрированы по приглашению!")
        else:
            # Если уже в базе, просто игнорируем реферал, но даем пройти дальше
            pass

    # 3. Базовая регистрация (если зашел без параметров и его нет в базе)
    if not is_registered:
        await register_user(tg_id=tg_id, name=name, invited_by=None)

    # 4. Финальный ответ с кнопкой запуска Mini App
    await message.answer(
        f"Добро пожаловать, {name}! Нажми на кнопку ниже, чтобы войти в сервис:",
        reply_markup=miniapp_keyboard(),
    )
