import uuid
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from utils.tariffs import TARIFFS, period_to_months
from keyboards.menu_kb import miniapp_keyboard
from utils.api import DjangoAPI

router = Router()
django_api = DjangoAPI()


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
    is_registered = await django_api.user_exists(tg_id=tg_id)

    # 2. Обработка аргументов (если они есть)
    if args:
        # --- Реферальная ссылка ---
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
            await django_api.register_user(
                tg_id=tg_id, name=name, invited_by=referrer_id
            )
            await message.answer("🎉 Вы успешно зарегистрированы по приглашению!")
        else:
            # Если уже в базе, просто игнорируем реферал, но даем пройти дальше
            pass

    # 3. Базовая регистрация (если зашел без параметров и его нет в базе)
    if not is_registered:
        await django_api.register_user(tg_id=tg_id, name=name, invited_by=None)

    # 4. Финальный ответ с кнопкой запуска Mini App
    await message.answer(
        f"Добро пожаловать, {name}! Нажми на кнопку ниже, чтобы войти в сервис:",
        reply_markup=miniapp_keyboard(),
    )
