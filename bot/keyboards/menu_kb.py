from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


def miniapp_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url="https://your-domain.com/miniapp/"),
                )
            ]
        ]
    )
