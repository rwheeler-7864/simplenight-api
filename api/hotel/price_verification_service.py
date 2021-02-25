import abc
import decimal
from enum import Enum

from api import logger
from api.hotel.models.hotel_common_models import RoomRate
from api.hotel.adapters import adapter_service
from api.hotel.models.hotel_api_model import HotelPriceVerification


class PriceVerificationLogicModule(abc.ABC):
    def __init__(self, original_rate: RoomRate, verified_rate: RoomRate):
        self.original_rate = original_rate
        self.verified_rate = verified_rate

    @abc.abstractmethod
    def compare(self) -> HotelPriceVerification:
        pass


class PriceVerificationNoPriceChangeModule(PriceVerificationLogicModule):
    def compare(self) -> HotelPriceVerification:
        original_total = decimal.Decimal(0)
        verified_total = decimal.Decimal(0)
        if not self.verified_rate:
            message = "Could not find rate key in recheck response"
            logger.error({"message": message, "verified_rate": self.verified_rate})
            raise ValueError(message)

        original_total += self.original_rate.total.amount
        verified_total += self.verified_rate.total.amount

        price_difference = verified_total - original_total
        allowed_difference = price_difference <= 0
        is_exact_price = price_difference == 0

        return HotelPriceVerification(
            is_allowed_change=allowed_difference,
            is_exact_price=is_exact_price,
            verified_room_rate=self.verified_rate,
            original_total=original_total,
            recheck_total=verified_total,
            price_difference=price_difference,
        )


class PriceVerificationModel(Enum):
    DEFAULT = PriceVerificationNoPriceChangeModule


def get_price_verification_model(
    original_rate: RoomRate,
    verified_rate: RoomRate,
    model_type: PriceVerificationModel = PriceVerificationModel.DEFAULT,
):
    model = model_type.value
    return model(original_rate, verified_rate)


def recheck(provider: str, room_rate: RoomRate) -> HotelPriceVerification:
    """
    Verify room prices with a particular HotelAdapter.  Detect price changes
    between the room rates.  Apply a validator to determine if the price change is allowed.
    If price change is not allowed, return an error.
    """

    adapter = adapter_service.get_adapter(name=provider)

    verified_room_rate = adapter.recheck(room_rate)

    model = get_price_verification_model(room_rate, verified_room_rate)
    return model.compare()
