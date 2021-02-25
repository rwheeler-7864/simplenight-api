import uuid
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

import requests_mock

from api.activities import activity_service
from api.activities.activity_models import SimplenightActivityDetailRequest, SimplenightActivityVariantRequest
from api.activities.adapters.tiqets.tiqets_activity_adapter import TiqetsActivityAdapter
from api.activities.adapters.tiqets.tiqets_transport import TiqetsTransport
from api.booking import booking_service
from api.hotel.models.booking_model import MultiProductBookingRequest, ActivityBookingRequest, ActivityBookingItem
from api.models.models import Feature, Booking, ActivityBookingModel, ActivityBookingItemModel
from api.multi.multi_product_models import ActivitySpecificSearch, ActivityLocationSearch
from api.tests import model_helper, test_objects
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.tests.utils import load_test_resource


class TestActivityService(SimplenightTestCase):
    @classmethod
    def setUpTestData(cls):
        latitude = 37.774930  # San Francisco
        longitude = -122.419420

        test_city = model_helper.create_geoname("12345", "City", "CA", "US", latitude=latitude, longitude=longitude)
        model_helper.create_geoname_altname(1, test_city, "en", "Test City Alt Name")

    def test_activity_search(self):
        search = ActivitySpecificSearch(
            begin_date=date(2020, 1, 1), end_date=date(2020, 1, 5), adults=1, children=0, activity_id="123"
        )

        activity = activity_service.search_by_id(search)
        self.assertIsNotNone(activity)
        self.assertIsNotNone(activity.name)
        self.assertIsNotNone(activity.description)
        self.assertIsNotNone(activity.activity_date)
        self.assertIsNotNone(activity.total_price)

    def test_activity_search_by_location(self):
        search = ActivityLocationSearch(
            begin_date=date(2020, 1, 1), end_date=date(2020, 1, 5), adults=1, children=0, location_id="12345"
        )

        results = activity_service.search_by_location(search)
        self.assertIsNotNone(results)

        activity = results[0]
        self.assertIsNotNone(activity)
        self.assertIsNotNone(activity.name)
        self.assertIsNotNone(activity.description)

    def test_activity_booking(self):
        self.stub_feature(Feature.ENABLED_ADAPTERS, TiqetsActivityAdapter.get_provider_name())

        begin_date = date(2020, 1, 1)
        end_date = date(2020, 1, 5)
        search = ActivityLocationSearch(begin_date=begin_date, end_date=end_date, adults=1, location_id="12345")
        transport = TiqetsTransport(test_mode=True)

        # First, perform an activity search, with response from Tiqets/Supplier API mocked
        availability_resource = load_test_resource("tiqets/tiqets-search-response.json")
        with requests_mock.Mocker() as mocker:
            mocker.post(transport.get_endpoint(TiqetsTransport.Endpoint.SEARCH), text=availability_resource)
            availability_results = activity_service.search_by_location(search)

        self.assertEqual(34, len(availability_results))
        self.assertEqual("San Francisco Museum of Modern Art (SFMOMA)", availability_results[0].name)
        self.assertIsNotNone(availability_results[0].code)

        # Second, retrieve activity details, with response mocked
        details_resource = load_test_resource("tiqets/tiqets-details-response.json")
        with requests_mock.Mocker() as mocker:
            mocker.get(requests_mock.ANY, text=details_resource)
            details_response = activity_service.details(
                SimplenightActivityDetailRequest(
                    code=availability_results[0].code, date_from=begin_date, date_to=end_date
                )
            )

        self.assertEqual(104, len(details_response.availabilities))

        activity_date = details_response.availabilities[0]

        # Third, retrieve ticket variants for the activity, using mock response
        variants_resource = load_test_resource("tiqets/tiqets-variant-response.json")
        with requests_mock.Mocker() as mocker:
            mocker.get(requests_mock.ANY, text=variants_resource)
            variant_response = activity_service.variants(
                SimplenightActivityVariantRequest(code=availability_results[0].code, activity_date=activity_date)
            )

        self.assertIsNotNone(variant_response.variants)
        self.assertIn("whole_day", variant_response.variants)
        self.assertEqual("2636", variant_response.variants["whole_day"][0].code)

        ticket_variant = variant_response.variants["whole_day"][0]
        booking_request = MultiProductBookingRequest(
            api_version=1,
            transaction_id=str(uuid.uuid4()),
            language="en",
            customer=test_objects.customer("John", "Simplenight"),
            payment=test_objects.payment("4242424242424242"),
            activity_booking=ActivityBookingRequest(
                code=availability_results[0].code,
                language_code="en",
                activity_date=activity_date,
                activity_time=time(12, 00),
                currency="USD",
                items=[
                    ActivityBookingItem(code=ticket_variant.code, quantity=2),
                    ActivityBookingItem(code=ticket_variant.code, quantity=1),
                ],
            ),
        )

        booking_resource = load_test_resource("tiqets/tiqets-book-response.json")
        with requests_mock.Mocker() as mocker:
            mocker.post(transport.get_endpoint(TiqetsTransport.Endpoint.BOOK), text=booking_resource)
            with patch("stripe.Token.create") as stripe_token_mock:
                stripe_token_mock.return_value = {"id": "tok_foo"}

                with patch("stripe.Charge.create") as stripe_create_mock:
                    stripe_create_mock.return_value = {
                        "currency": "USD",
                        "id": "payment-id",
                        "amount": 100.00,
                        "object": "settled",
                    }

                    booking = booking_service.book(booking_request)

        persisted_booking = Booking.objects.get(transaction_id=booking.transaction_id)
        persisted_activity = ActivityBookingModel.objects.get(booking=persisted_booking)
        persisted_items = ActivityBookingItemModel.objects.filter(activity_reservation=persisted_activity)

        self.assertEqual(2, len(persisted_items))
        self.assertEqual(Decimal("49.99"), persisted_activity.total_price)
