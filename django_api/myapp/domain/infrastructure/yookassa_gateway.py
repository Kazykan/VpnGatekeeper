# myapp/domain/infrastructure/yookassa_gateway.py
from yookassa import Payment
from django.conf import settings

def create_yookassa_payment(amount_rub: int, description: str, save_method: bool, metadata: dict):
    # amount_rub — целые рубли
    return Payment.create({
        "amount": {"value": f"{int(amount_rub)}.00", "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": settings.YOOKASSA_RETURN_URL},
        "capture": True,
        "save_payment_method": save_method,
        "description": description,
        "metadata": metadata,
    }, settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_API_KEY)
