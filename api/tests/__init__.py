import decimal

from api.hotel.models.hotel_common_models import Money


def to_money(amount: str, currency="USD"):
    return Money(amount=decimal.Decimal(amount), currency=currency)
