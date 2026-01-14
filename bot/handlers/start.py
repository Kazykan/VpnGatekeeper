from aiogram import Router, types
from aiogram.filters import Command
from keyboards.menu_kb import miniapp_keyboard
from utils.api import register_user, user_exists

router = Router()


def register_start_handlers(dp):
    dp.include_router(router)


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user is None or message.text is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user = message.from_user
    tg_id = user.id
    name = user.username or user.full_name if user else ""

    # referral
    args = message.text.split(maxsplit=1)
    referral_id = int(args[1]) if len(args) > 1 else None

    if referral_id == user.id:  # Защита от саморефералов
        referral_id = None

    if not await user_exists(tg_id=tg_id):
        await register_user(tg_id=tg_id, name=name, invited_by=referral_id)

    # Отправляем кнопку Mini App
    await message.answer(
        f"Добро пожаловать! Открывай приложение:",
        reply_markup=miniapp_keyboard(),
    )
