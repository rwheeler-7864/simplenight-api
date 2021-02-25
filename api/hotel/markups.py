import uuid
from decimal import Decimal

from api.hotel.models.hotel_common_models import Money, RoomRate

DEFAULT_MARKUP = Decimal("0.12")


def markup_rate(room_rate: RoomRate) -> RoomRate:
    new_room_rate_code = str(uuid.uuid4())[:8]

    return RoomRate(
        code=new_room_rate_code,
        room_type_code=room_rate.room_type_code,
        rate_plan_code=room_rate.rate_plan_code,
        rate_type=room_rate.rate_type,
        total_base_rate=markup(room_rate.total_base_rate),
        total_tax_rate=markup(room_rate.total_tax_rate),
        total=markup(room_rate.total),
        maximum_allowed_occupancy=room_rate.maximum_allowed_occupancy,
        daily_rates=room_rate.daily_rates,
        partner_data=room_rate.partner_data,
        postpaid_fees=room_rate.postpaid_fees,
    )


def markup(total: Money):
    markup_pct = get_default_markup()
    markup_price = round(total.amount * markup_pct, 2)

    return Money(amount=markup_price, currency=total.currency)


def get_default_markup():
    return DEFAULT_MARKUP + 1
