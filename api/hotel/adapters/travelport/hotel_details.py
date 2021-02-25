from datetime import date
from typing import Dict, Any, Optional, Union

from api.hotel.models.hotel_api_model import HotelDetailsSearchRequest
from api.hotel.adapters.travelport.settings import TARGET_BRANCH


class TravelportHotelDetailsBuilder:
    def __init__(self):
        self._request: Dict[Any, Any] = {
            "TargetBranch": TARGET_BRANCH,
            "BillingPointOfSaleInfo": {"OriginApplication": "Simplenight"},
            "HotelProperty": {},
            "HotelDetailsModifiers": {"RateRuleDetail": "Complete", "HotelStay": {}},
        }

    @staticmethod
    def build(hotel_details_request: HotelDetailsSearchRequest):
        hotel_details_builder = TravelportHotelDetailsBuilder()
        hotel_details_builder.chain_code = hotel_details_request.chain_code
        hotel_details_builder.hotel_code = hotel_details_request.hotel_code
        hotel_details_builder.checkin = hotel_details_request.start_date
        hotel_details_builder.checkout = hotel_details_request.end_date
        hotel_details_builder.num_rooms = hotel_details_request.num_rooms
        hotel_details_builder.currency = hotel_details_request.currency

        return hotel_details_builder.request

    @property
    def request(self):
        return self._request

    @property
    def chain_code(self):
        return self.request.get("HotelProperty", {}).get("HotelChain")

    @chain_code.setter
    def chain_code(self, hotel_chain):
        self.request["HotelProperty"]["HotelChain"] = hotel_chain

    @property
    def hotel_code(self):
        return self.request.get("HotelProperty", {}).get("HotelCode")

    @hotel_code.setter
    def hotel_code(self, hotel_code):
        self.request["HotelProperty"]["HotelCode"] = hotel_code

    @property
    def checkin(self) -> Optional[date]:
        checkin_date = self._hotel_stay.get("CheckinDate")
        return date.fromisoformat(checkin_date)

    @checkin.setter
    def checkin(self, checkin: Union[date, str]):
        if isinstance(checkin, date):
            checkin = str(checkin)

        self._hotel_stay["CheckinDate"] = checkin

    @property
    def checkout(self) -> Optional[date]:
        checkout_date = self._hotel_stay.get("CheckoutDate")
        return date.fromisoformat(checkout_date)

    @checkout.setter
    def checkout(self, checkout: Union[date, str]):
        if isinstance(checkout, date):
            checkout = str(checkout)

        self._hotel_stay["CheckoutDate"] = checkout

    @property
    def num_rooms(self):
        return self.request["HotelDetailsModifiers"].get("NumberOfRooms")

    @num_rooms.setter
    def num_rooms(self, num_rooms):
        self.request["HotelDetailsModifiers"]["NumberOfRooms"] = num_rooms

    @property
    def currency(self):
        return self.request["HotelDetailsModifiers"]["PreferredCurrency"]

    @currency.setter
    def currency(self, currency):
        self.request["HotelDetailsModifiers"]["PreferredCurrency"] = currency

    @property
    def _hotel_stay(self):
        return self.request["HotelDetailsModifiers"]["HotelStay"]
