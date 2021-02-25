import abc
from datetime import date
from decimal import Decimal
from typing import List, Any, Dict, Optional

from api import logger
from api.activities.activity_adapter import ActivityAdapter
from api.activities.activity_internal_models import (
    AdapterActivity,
    AdapterActivitySpecificSearch,
    AdapterActivityLocationSearch,
    AdapterActivityBookingResponse,
    ActivityLocation,
)
from api.activities.activity_models import (
    SimplenightActivityDetailResponse,
    ActivityCancellation,
    ActivityItem,
    ActivityVariants,
    ActivityVariant,
)
from api.activities.adapters.suppliers_api.suppliers_api_transport import SuppliersApiTransport
from api.common.common_models import BusinessContact
from api.hotel.models.booking_model import Customer, Locator, AdapterActivityBookingRequest
from api.hotel.models.hotel_api_model import Image, ImageType
from api.hotel.models.hotel_common_models import Money
from api.view.exceptions import BookingException, BookingErrorCode


class SuppliersApiActivityAdapter(ActivityAdapter, abc.ABC):
    def __init__(self, transport: SuppliersApiTransport):
        self.transport = transport

    async def search_by_location(self, search: AdapterActivityLocationSearch) -> List[AdapterActivity]:
        request_params = self._get_search_params(search)
        logger.info(f"Searching {self.get_provider_name()} with params: {request_params}")
        response = self.transport.search(**request_params)

        return list(map(lambda x: self._create_activity(x, activity_date=search.begin_date), response["data"]))

    async def search_by_id(self, search: AdapterActivitySpecificSearch) -> AdapterActivity:
        raise NotImplementedError("Search by ID Not Implemented")

    async def book(self, request: AdapterActivityBookingRequest, customer: Customer) -> AdapterActivityBookingResponse:
        params = {
            "code": request.code,
            "date": str(request.activity_date),
            "time": str(request.activity_time),
            "currency": request.currency,
            "supplier_proceeds": str(sum(x.price for x in request.items)),
            "booking": {
                "customer": {
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "email": customer.email,
                    "phone": customer.phone_number,
                    "locale": request.language_code,
                    "country": customer.country,
                    "salutation": customer.salutation,
                }
            },
            "items": [
                {
                    "code": request.items[0].code,
                    "quantity": 1,
                    "supplier_proceeds": str(request.items[0].price),
                    "channel_proceeds": 0,
                    "date": str(request.activity_date),
                }
            ],
        }

        response = self.transport.book(**params)
        if not response or not response["success"]:
            logger.warn(f"Error during booking: {response}")
            raise BookingException(error_type=BookingErrorCode.PROVIDER_BOOKING_FAILURE, detail="Error in booking")

        return AdapterActivityBookingResponse(
            success=response["success"], record_locator=Locator(id=response["order_id"])
        )

    async def details(self, product_id: str, date_from: date, date_to: date) -> SimplenightActivityDetailResponse:
        response = self.transport.details(product_id, date_from, date_to)
        details = self._create_details(response)

        return details

    async def variants(self, product_id: str, activity_date: date) -> ActivityVariants:
        response = self.transport.variants(product_id, activity_date)
        parsed_variants = {
            activity_time: list(map(self._parse_variants, variants)) for activity_time, variants in response.items()
        }

        variants = ActivityVariants(variants=parsed_variants)
        return variants

    async def cancel(self, order_id: str) -> bool:
        pass

    @staticmethod
    def _parse_variants(variant):
        additional_info = {}
        if "additional" in variant:
            additional_info = variant["additional"]

        return ActivityVariant(
            code=variant["code"],
            name=variant["name"],
            description=variant["description"],
            price=Decimal(variant["price"]),
            capacity=variant["capacity"],
            additional=additional_info,
        )

    @staticmethod
    def _parse_image(image: Dict, display_order: int) -> Image:
        return Image(url=image["url"], type=ImageType.UNKNOWN, display_order=display_order)

    @staticmethod
    def _parse_location(locations) -> Optional[ActivityLocation]:
        try:
            return ActivityLocation(
                address=locations[0]["address"], latitude=locations[0]["latitude"], longitude=locations[0]["longitude"],
            )
        except KeyError:
            return None

    @staticmethod
    def _parse_cancellation_policy(policy):
        return ActivityCancellation(type=policy["type"], label=policy["label"])

    @staticmethod
    def _parse_activity_items(item):
        return ActivityItem(
            category=item["categories"],
            code=item["code"],
            status=item["status"],
            price=Decimal(item["price"]),
            price_type=item["price_type"],
        )

    def _create_details(self, detail):
        logger.info("Found activity details: ", detail)
        availabilities = map(lambda x: date.fromisoformat(x), detail["availabilities"])

        return SimplenightActivityDetailResponse(
            code=detail["code"],
            type=detail["type"],
            categories=detail["categories"],
            timezone=detail["timezone"],
            images=list(self._parse_image(image, idx) for idx, image in enumerate(detail["images"])),
            contact=BusinessContact(
                name=detail["contact"]["name"],
                email=detail["contact"]["email"],
                website=detail["contact"]["website"],
                address=detail["contact"]["address"],
                phones=detail["contact"]["phones"],
            ),
            locations=self._parse_location(detail["locations"]),
            availabilities=list(availabilities),
            policies=detail["policies"],
            cancellations=list(map(self._parse_cancellation_policy, detail["cancellations"])),
        )

    def _create_activity(self, activity, activity_date: date):
        rating = None
        if "rating" in activity and activity["rating"]:
            rating = Decimal(activity["rating"])

        reviews = 0
        if "reviews" in activity and activity["reviews"]:
            reviews = activity["reviews"]

        return AdapterActivity(
            name=activity["name"],
            provider=self.get_provider_name(),
            code=activity["code"],
            description=activity["description"],
            activity_date=activity_date,
            total_price=Money(amount=activity["price"], currency=activity["currency"]),
            categories=activity["categories"],
            images=list(self._parse_image(image, idx) for idx, image in enumerate(activity["images"])),
            reviews=reviews,
            rating=rating,
            location=self._parse_location(activity["locations"]),
        )

    @staticmethod
    def _get_search_params(search: AdapterActivityLocationSearch) -> Dict[Any, Any]:
        return {
            "date_from": str(search.begin_date),
            "date_to": str(search.end_date),
            "location": {"longitude": str(search.location.longitude), "latitude": str(search.location.latitude)},
        }
