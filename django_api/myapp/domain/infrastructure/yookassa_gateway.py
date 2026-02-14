import uuid
from yookassa import Payment as YkPayment, Configuration
from django.conf import settings


def _setup_yookassa():
    """Внутренний помощник для инициализации конфига"""
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_API_KEY


def create_yookassa_payment(
    amount_rub: int, description: str, save_method: bool, metadata: dict
):
    _setup_yookassa()
    payment_data = {
        "amount": {"value": f"{int(amount_rub)}.00", "currency": "RUB"},
        "confirmation": {"type": "embedded"},
        "capture": True,
        "save_payment_method": save_method,
        "description": description,
        "metadata": metadata,
    }
    idempotency_key = str(uuid.uuid4())
    return YkPayment.create(payment_data, idempotency_key)


def create_recurring_payment(amount_rub, payment_method_id, description, metadata):
    _setup_yookassa()
    return YkPayment.create(
        {
            "amount": {"value": str(amount_rub), "currency": "RUB"},
            "capture": True,
            "payment_method_id": payment_method_id,
            "description": description,
            "metadata": metadata,
        }
    )


def get_payment_info(provider_payment_id: str):
    """Получает актуальный статус платежа из ЮKassa"""
    _setup_yookassa()
    return YkPayment.find_one(provider_payment_id)
