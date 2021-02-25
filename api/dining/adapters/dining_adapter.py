import abc
from typing import List

from api.common.base_adapter import BaseAdapter
from api.dining.models.dining_api_model import (
    AdapterDining,
    AdapterOpening,
    DiningSearch,
    OpeningSearch,
    DiningDetail,
    DiningReview,
    DiningReservationRequest,
    DiningReservation,
    AdapterCancelRequest,
)


class DiningAdapter(BaseAdapter, abc.ABC):
    @abc.abstractmethod
    def get_businesses(self, search: DiningSearch) -> List[AdapterDining]:
        """Search businesses for provided queries"""

    @abc.abstractmethod
    def get_openings(self, search: OpeningSearch) -> List[AdapterOpening]:
        """Search available time slot for provided queries"""

    @abc.abstractmethod
    def details(self, *args) -> DiningDetail:
        """Return Dining Details"""

    @abc.abstractmethod
    def reviews(self, *args) -> List[DiningReview]:
        """Returns a list of user reviews"""

    @abc.abstractmethod
    def book(self, request: DiningReservationRequest) -> DiningReservation:
        """Given a HotelBookingRequest, confirm a reservation with a hotel provider"""

    @abc.abstractmethod
    def cancel(self, booking_id: str):
        """Given an adapter record locator, cancel a booking."""
