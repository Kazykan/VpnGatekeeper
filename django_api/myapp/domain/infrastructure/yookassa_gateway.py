import uuid
from yookassa import Payment as YkPayment, Configuration
from django.conf import settings


def create_yookassa_payment(
    amount_rub: int, description: str, save_method: bool, metadata: dict
):
    # 1. Настраиваем авторизацию (SDK берет данные отсюда автоматически)
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_API_KEY

    # 2. Формируем тело запроса
    payment_data = {
        "amount": {"value": f"{int(amount_rub)}.00", "currency": "RUB"},
        "confirmation": {"type": "embedded"},
        "capture": True,
        "save_payment_method": save_method,
        "description": description,
        "metadata": metadata,
    }

    # 3. Генерируем ключ идемпотентности.
    # Он защищает от повторных списаний при сетевых сбоях.
    idempotency_key = str(uuid.uuid4())

    # 4. Вызываем создание платежа.
    # Теперь передается ровно 2 позиционных аргумента.
    return YkPayment.create(payment_data, idempotency_key)


def create_recurring_payment(amount_rub, payment_method_id, description, metadata):
    return YkPayment.create(
        {
            "amount": {"value": str(amount_rub), "currency": "RUB"},
            "capture": True,  # Списываем сразу
            "payment_method_id": payment_method_id,
            "description": description,
            "metadata": metadata,
        }
    )
