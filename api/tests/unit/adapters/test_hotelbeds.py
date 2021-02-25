from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import requests_mock

from api.hotel.adapters.hotelbeds.hotelbeds_adapter import HotelbedsAdapter
from api.hotel.adapters.hotelbeds.hotelbeds_transport import HotelbedsTransport
from api.hotel.models.adapter_models import AdapterLocationSearch, AdapterOccupancy
from api.hotel.models.booking_model import HotelBookingRequest, Customer, Traveler
from api.hotel.models.hotel_common_models import RoomOccupancy
from api.locations.models import LocationType, Location
from api.tests import test_objects, model_helper
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.tests.utils import load_test_resource


class TestHotelBeds(SimplenightTestCase):
    def test_default_headers_in_transport(self):
        transport = HotelbedsTransport()
        default_headers = transport._get_headers()
        self.assertIn("Api-Key", default_headers)
        self.assertIn("X-Signature", default_headers)
        self.assertEqual("gzip", default_headers["Accept-Encoding"])
        self.assertEqual("application/json", default_headers["Content-Type"])

        headers = transport._get_headers(foo="bar")
        self.assertIn("Api-Key", headers)
        self.assertEqual("bar", headers["foo"])

    def test_headers_return_copy(self):
        transport = HotelbedsTransport()
        transport._get_headers()["foo"] = "bar"
        self.assertNotIn("foo", transport._get_headers())

    def test_hotelbeds_search_by_location_parsing(self):
        # Create test provider hotels, which are required for HotelBeds to return availability
        provider = model_helper.create_provider(HotelbedsAdapter.get_provider_name())
        model_helper.create_provider_hotel(provider, "349168", "Hotel One")
        model_helper.create_provider_hotel(provider, "97334", "Hotel Two")

        model_helper.create_provider_image(provider, "349168", "http://foo.image")
        model_helper.create_provider_image(provider, "97334", "http://foo.image")

        resource = load_test_resource("hotelbeds/search-by-location-response.json")
        hotelbeds = HotelbedsAdapter()

        search = AdapterLocationSearch(
            location_id="FOO",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 7),
            occupancy=AdapterOccupancy(adults=1),
        )

        transport = HotelbedsTransport()
        hotels_url = transport.endpoint(transport.Endpoint.HOTELS)

        with patch("api.hotel.adapters.hotelbeds.hotelbeds_adapter.find_city_by_simplenight_id") as mock_find_city:
            mock_find_city.return_value = Location(
                location_id="SFO",
                language_code="en",
                location_name="San Francisco",
                iso_country_code="US",
                latitude=Decimal("37.774930"),
                longitude=Decimal("-122.419420"),
                location_type=LocationType.CITY,
            )

            with requests_mock.Mocker() as mocker:
                mocker.post(hotels_url, text=resource)
                results = hotelbeds.search_by_location(search)

            hotel = results[0]
            self.assertEqual("349168", hotel.hotel_id)
            self.assertEqual("2020-01-01", hotel.start_date.strftime("%Y-%m-%d"))
            self.assertEqual("2020-01-07", hotel.end_date.strftime("%Y-%m-%d"))
            self.assertEqual(1, hotel.occupancy.adults)
            self.assertEqual(0, hotel.occupancy.children)

            room_type = hotel.room_types[0]
            self.assertEqual(9, len(hotel.room_types))
            self.assertEqual("DBL.QN", room_type.code)
            self.assertEqual("DOUBLE QUEEN SIZE BED", room_type.name)
            self.assertEqual("DOUBLE QUEEN SIZE BED", room_type.description)
            self.assertEqual(1, room_type.capacity.adults)
            self.assertEqual(0, room_type.capacity.children)

            room_rate = hotel.room_rates[0]
            expected_rate_key = (
                "20200728|20200802|W|256|349168|DBL.QN|ID_B2B_19|RO|RATE1|1~1~0||N@03~~21164~299946933~N"
                "~AC7BF302F70841C159337089520200AAUK0000024002300060121164"
            )
            self.assertEqual(36, len(hotel.room_rates))
            self.assertEqual(expected_rate_key, room_rate.code)
            self.assertEqual("DBL.QN", room_rate.room_type_code)
            self.assertEqual(expected_rate_key, room_rate.rate_plan_code)
            self.assertEqual(Decimal("100.17"), room_rate.total_base_rate.amount)
            self.assertEqual(Decimal("113.00"), room_rate.total_tax_rate.amount)
            self.assertEqual(Decimal("213.17"), room_rate.total.amount)

    def test_hotelbeds_booking(self):
        room_rate = test_objects.room_rate(rate_key="rate-key", total="0")

        booking_request = HotelBookingRequest(
            api_version=1,
            transaction_id="tx",
            hotel_id="123",
            language="en",
            customer=Customer(
                first_name="John", last_name="Smith", phone_number="5558675309", email="john@smith.foo", country="US"
            ),
            traveler=Traveler(first_name="John", last_name="Smith", occupancy=RoomOccupancy(adults=1)),
            room_code=room_rate.code,
            payment=None,
        )

        transport = HotelbedsTransport()
        hotelbeds = HotelbedsAdapter(transport)
        booking_resource = load_test_resource("hotelbeds/booking-confirmation-response.json")
        booking_url = transport.endpoint(transport.Endpoint.BOOKING)
        with requests_mock.Mocker() as mocker:
            mocker.post(booking_url, text=booking_resource)
            booking_response = hotelbeds.book(booking_request)

        self.assertIsNotNone(booking_response)

    # def test_hotelbeds_recheck(self):
    #     search_request = self.create_location_search(location_id="SFO")

    #     avail_response = load_test_resource("hotelbeds/recheck/availability.json")
    #     recheck_response = load_test_resource("hotelbeds/recheck/recheck.json")

    #     transport = HotelbedsTransport()
    #     hotelbeds = HotelbedsAdapter(transport)
    #     hotels_url = transport.endpoint(transport.Endpoint.HOTELS)
    #     checkrates_url = transport.endpoint(transport.Endpoint.CHECKRATES)

    #     with patch("api.locations.location_service.find_provider_location") as mock_location_service:
    #         mock_location_service.return_value = model_helper.create_provider_city(
    #             provider_name=HotelbedsAdapter.get_provider_name(),
    #             code="SFO",
    #             name="San Francisco",
    #             province="CA",
    #             country="US",
    #         )

    #         with requests_mock.Mocker() as mocker:
    #             mocker.post(hotels_url, text=avail_response)
    #             mocker.post(checkrates_url, text=recheck_response)

    #             hotels = hotelbeds.search_by_location(search_request)
    #             assert len(hotels) > 0

    #             availability_room_rates = hotels[0].room_rates[0]
    #             recheck_response = hotelbeds.recheck(availability_room_rates)

    #             self.assertEqual(Decimal("99.89"), availability_room_rates.total.amount)
    #             self.assertEqual(Decimal("149.84"), recheck_response.total.amount)

    @staticmethod
    def create_location_search(location_id="TVL"):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search_request = AdapterLocationSearch(
            location_id=location_id, start_date=checkin, end_date=checkout, occupancy=AdapterOccupancy(),
        )

        return search_request
