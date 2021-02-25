from typing import List

from api import logger
from api.dining.adapters.dining_adapter import DiningAdapter
from api.dining.adapters.yelp.yelp_transport import YelpTransport
from api.common.common_models import from_json
from api.dining.models.dining_api_model import (
    DiningBase,
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
from api.view.exceptions import AvailabilityException, AvailabilityErrorCode


class YelpAdapter(DiningAdapter):
    def __init__(self, transport=None):
        self.transport = transport
        if self.transport is None:
            self.transport = YelpTransport(test_mode=True)

    def get_businesses(self, search: DiningSearch) -> List[AdapterDining]:
        if search.date and search.time and search.covers:
            request = self._create_business_search(search)
        else:
            request = self._create_location_search(search)

        print(request)
        response = self.transport.businesses(params=request)
        dining_results = self._check_operation_response_and_get_results(response, "businesses")

        if len(dining_results) == 0:
            return []

        dinings = self._create_dinings_from_response(search, dining_results)

        return dinings

    def get_openings(self, search: OpeningSearch) -> List[AdapterOpening]:
        request = self._create_base_search(search)
        response = self.transport.business_openings(id=search.dining_id, params=request)
        opening_results = self._check_operation_response_and_get_results(response, "reservation_times")

        if len(opening_results) == 0:
            return []

        dinings = self._create_openings_from_response(search, opening_results)

        return dinings

    def details(self, search) -> DiningDetail:
        response = self.transport.business_details(id=search.dining_id, params={})
        dining_detail = DiningDetail(
            dining_id=search.dining_id,
            name=response["name"],
            rating=response["rating"],
            phone=response["phone"],
            images=response["photos"],
            location={
                **response["coordinates"],
                "address": ", ".join(str(x) for x in response["location"]["display_address"]),
            },
        )

        return dining_detail

    def reviews(self, search) -> List[DiningReview]:
        response = self.transport.business_reviews(id=search.dining_id, params={})
        review_results = self._check_operation_response_and_get_results(response, "reviews")

        if len(review_results) == 0:
            return []

        reviews = self._create_reviews_from_response(search, review_results)

        return reviews

    def book(self, request: DiningReservationRequest) -> DiningReservation:
        hold_params = {
            **self._create_base_search(request),
            "unique_id": request.user_id,
        }
        response = self.transport.booking_hold(id=request.dining_id, params=hold_params)
        hold_result = self._check_operation_response_and_get_results(response, "")

        booking_params = {
            **self._create_base_search(request),
            **request.customer.__dict__,
            "unique_id": request.user_id,
            "hold_id": hold_result["hold_id"],
        }
        response = self.transport.booking(id=request.dining_id, params=booking_params)
        booking_result = self._check_operation_response_and_get_results(response, "")

        return DiningReservation(note=booking_result["notes"], booking_id=booking_result["reservation_id"])

    def cancel(self, booking_id: str):
        response = self.transport.booking_cancel(id=booking_id, params={})
        self._check_operation_response_and_get_results(response, "")

        return

    def _create_business_search(self, search: DiningSearch):
        params = {
            **self._create_location_search(search),
            "reservation_date": search.date,
            "reservation_time": search.time,
            "reservation_covers": search.covers,
        }

        return params

    def _create_base_search(self, search: OpeningSearch):
        params = {
            "date": search.date,
            "time": search.time,
            "covers": search.covers,
        }

        return params

    def _create_openings_from_response(self, search, opening_result) -> List[AdapterDining]:
        result = []
        for opening in opening_result:
            result.append(AdapterOpening(date=opening["date"], times=[x["time"] for x in opening["times"]]))

        return result

    def _create_dinings_from_response(self, search, dining_results) -> List[AdapterDining]:
        result = []
        for dining in dining_results:
            result.append(
                AdapterDining(
                    dining_id=dining["id"],
                    name=dining["name"],
                    image=dining["image_url"],
                    rating=dining["rating"],
                    location={
                        **dining["coordinates"],
                        "address": ", ".join(str(x) for x in dining["location"]["display_address"]),
                    },
                    phone=dining["phone"],
                )
            )

        return result

    def _create_reviews_from_response(self, search, review_results) -> List[DiningReview]:
        result = []
        for review in review_results:
            result.append(
                DiningReview(
                    rating=review["rating"],
                    text=review["text"],
                    timestamp=review["time_created"],
                    user={
                        "name": review["user"]["name"],
                        "image": review["user"]["image_url"],
                    },
                )
            )

        return result

    def _create_dining_detail_from_response(self, dining_result) -> List[AdapterOpening]:
        result = []
        for opening in opening_results:
            result.append(AdapterOpening(date=opening["date"], times=[x["time"] for x in opening["times"]]))

        return result

    @classmethod
    def factory(cls, test_mode=True):
        return YelpAdapter(YelpTransport(test_mode=test_mode))

    @classmethod
    def get_provider_name(cls):
        return

    @staticmethod
    def _create_location_search(search: DiningSearch):
        params = {"latitude": search.latitude, "longitude": search.longitude}

        return params

    @staticmethod
    def _check_operation_response_and_get_results(response, operation):
        if response is None:
            raise AvailabilityException(
                error_type=AvailabilityErrorCode.PROVIDER_ERROR,
                detail="Could not retrieve response",
            )
        if "error" in response:
            error_message = response["error"]
            if "description" in error_message:
                error_message = error_message["description"]
            logger.error("Error in Yelp Message: " + error_message)
            raise AvailabilityException(error_type=AvailabilityErrorCode.PROVIDER_ERROR, detail=error_message)

        return response[operation] if operation else response
