from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import patch

import requests_mock
from freezegun import freeze_time

from api.common.common_models import from_json
from api.hotel import provider_cache_service
from api.hotel.adapters.hotelbeds.hotelbeds_adapter import HotelbedsAdapter
from api.hotel.adapters.hotelbeds.hotelbeds_transport import HotelbedsTransport
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.converter.google_models import (
    GoogleHotelSearchRequest,
    RoomParty,
    GoogleHotelApiResponse,
    GoogleBookingSubmitRequest,
    GoogleTraveler,
    GooglePayment,
    GooglePaymentCardParameters,
    GoogleBookingRoomRate,
    GoogleBookingResponse,
    GoogleStatus,
)
from api.hotel.models.booking_model import Customer, PaymentMethod, CardType
from api.hotel.models.hotel_api_model import (
    HotelSpecificSearch,
    HotelLocationSearch,
    SimplenightHotel,
)
from api.hotel.models.hotel_common_models import RoomOccupancy, Address
from api.locations.models import Location, LocationType
from api.models.models import Booking, Feature
from api.tests import test_objects, model_helper
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.tests.utils import load_test_resource

SEARCH_BY_ID = "/api/v1/hotels/search-by-id"
SEARCH_BY_LOCATION = "/api/v1/hotels/search-by-location"
BOOKING = "/api/v1/hotels/booking"
BOG_BOOKING = "/api/v1/hotels/google/booking"
BOG_SEARCH_BY_ID = "/api/v1/hotels/google/search-by-id"


class TestHotelsView(SimplenightTestCase):
    def test_search_by_id(self):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)

        search = HotelSpecificSearch(
            hotel_id="SN123",
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=1),
            provider="stub_hotel",
        )

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            with patch("api.hotel.hotel_mappings.find_provider_hotel_id") as mock_find_provider:
                mock_find_provider.return_value = "ABC123"
                response = self._post(SEARCH_BY_ID, search)

        self.assertEqual(200, response.status_code)

        hotel = SimplenightHotel.parse_raw(response.content)
        self.assertIsNotNone(hotel.hotel_id)
        self.assertEqual(10.0, hotel.hotel_details.review_rating)

    def test_search_by_location(self):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = HotelLocationSearch(
            start_date=checkin, end_date=checkout, occupancy=RoomOccupancy(adults=1), location_id="SFO"
        )

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            response = self._post(SEARCH_BY_LOCATION, search)

        self.assertEqual(200, response.status_code)

        hotels = from_json(response.content, SimplenightHotel, many=True)
        self.assertTrue(len(hotels) > 1)
        self.assertIsNotNone(hotels[0].hotel_id)

    def test_search_location_by_provider(self):
        provider = model_helper.create_provider(HotelbedsAdapter.get_provider_name())
        model_helper.create_provider_hotel(provider, "13517", "Hotel One")
        model_helper.create_provider_hotel(provider, "345972", "Hotel Two")

        model_helper.create_provider_image(provider, "13517", "http://img.foo")
        model_helper.create_provider_image(provider, "345972", "http://img.foo")

        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = HotelLocationSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=1),
            location_id="SFO",
            provider="hotelbeds",
        )

        hotelbeds_tranport = HotelbedsTransport(test_mode=True)
        saved_search_response = load_test_resource("hotelbeds/hotelbeds-search-lat-lon-response.json")
        search_endpoint = hotelbeds_tranport.endpoint(HotelbedsTransport.Endpoint.HOTELS)
        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "SFO"

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
                    mocker.post(search_endpoint, text=saved_search_response)
                    response = self._post(SEARCH_BY_LOCATION, search)

        self.assertEqual(200, response.status_code)

        hotels = from_json(response.content, SimplenightHotel, many=True)
        self.assertEqual(2, len(hotels))
        self.assertIsNotNone(hotels[0].hotel_id)

    def test_booking_invalid_payment(self):
        invalid_card_number_payment = test_objects.payment("4000000000000002")
        booking_request = test_objects.booking_request(
            rate_code="simplenight_rate_key", payment_obj=invalid_card_number_payment
        )

        hotel = test_objects.hotel()
        provider_room_rate = test_objects.room_rate(rate_key="rate_key", total="100.00")
        simplenight_room_rate = test_objects.room_rate(rate_key="simplenight_rate_key", total="120.00")
        provider_cache_service.save_provider_rate(
            hotel, room_rate=provider_room_rate, simplenight_rate=simplenight_room_rate
        )

        response = self.post(endpoint=BOOKING, obj=booking_request)

        self.assertEqual(500, response.status_code)
        self.assertIn("error", response.json())
        self.assertIn("Your card was declined", response.json()["error"]["message"])
        self.assertEqual("PAYMENT_DECLINED", response.json()["error"]["type"])
        print(response.json())

    def test_booking_unhandled_error(self):
        invalid_card_number_payment = test_objects.payment("4242424242424242")
        booking_request = test_objects.booking_request(
            rate_code="simplenight_rate_key", payment_obj=invalid_card_number_payment
        )

        hotel = test_objects.hotel()
        provider_room_rate = test_objects.room_rate(rate_key="rate_key", total="100.00")
        simplenight_room_rate = test_objects.room_rate(rate_key="simplenight_rate_key", total="120.00")
        provider_cache_service.save_provider_rate(
            hotel, room_rate=provider_room_rate, simplenight_rate=simplenight_room_rate
        )

        with patch("api.booking.booking_service._persist_booking_record", side_effect=Exception("Boom")):
            response = self.post(endpoint=BOOKING, obj=booking_request)

        self.assertEqual(500, response.status_code)
        self.assertIn("error", response.json())
        self.assertIn("Boom", response.json()["error"]["message"])
        self.assertEqual("UNHANDLED_ERROR", response.json()["error"]["type"])

    def test_availability_error_included_in_api_rest(self):
        model_helper.create_provider(HotelbedsAdapter.get_provider_name())

        error_response = load_test_resource("hotelbeds/error-response.json")
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
                mocker.post(hotels_url, text=error_response)
                search_request = HotelLocationSearch(
                    location_id="SFO",
                    start_date=date(2020, 1, 20),
                    end_date=date(2020, 1, 27),
                    occupancy=RoomOccupancy(adults=2, children=1),
                    provider="hotelbeds",
                )

                response = self.post(endpoint=SEARCH_BY_LOCATION, obj=search_request)
                body = response.json()
                assert body is not None
                assert body["detail"] == "Invalid data. The check-in must be in the future."
                assert body["status_code"] == 500

    @freeze_time("2020-01-01")
    def test_book_on_google_hotel_availability_and_booking(self):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = GoogleHotelSearchRequest(
            api_version=1,
            transaction_id="foo",
            hotel_id="ABC123",
            start_date=checkin,
            end_date=checkout,
            party=RoomParty(children=[10], adults=1),
        )

        self.stub_feature(Feature.TEST_MODE, True)
        self.stub_feature(Feature.ENABLED_ADAPTERS, "priceline")

        priceline_hotel_id_response = load_test_resource("priceline/bog1-availability-response.json")
        transport = PricelineTransport(test_mode=True)

        avail_endpoint = transport.endpoint(transport.Endpoint.HOTEL_EXPRESS)
        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            with patch("api.hotel.hotel_mappings.find_provider_hotel_id") as mock_find_provider:
                mock_find_provider.return_value = "700363264"
                with requests_mock.Mocker() as mocker:
                    mocker.get(avail_endpoint, text=priceline_hotel_id_response)
                    response = self._post(endpoint=BOG_SEARCH_BY_ID, data=search)

        self.assertEqual(200, response.status_code)

        availability_resp_obj = from_json(response.json(), GoogleHotelApiResponse)
        self.assertIsNotNone(availability_resp_obj)
        self.assertEqual(1, availability_resp_obj.api_version)
        self.assertEqual("foo", availability_resp_obj.transaction_id)
        self.assertEqual("123", availability_resp_obj.hotel_id)
        self.assertEqual("2020-01-31", str(availability_resp_obj.start_date))
        self.assertEqual("2020-02-05", str(availability_resp_obj.end_date))
        self.assertEqual([10], availability_resp_obj.party.children)
        self.assertEqual(1, availability_resp_obj.party.adults)
        self.assertEqual("8qJgpBN4M9htbX00RAAmhlGt4vL5QM2kEibAktNLe3M", availability_resp_obj.room_types[0].code)
        self.assertAlmostEqual(953.91, float(availability_resp_obj.room_rates[0].total_price_at_booking.amount), 0)

        self.assertIsNotNone(availability_resp_obj.room_rates[0].line_items)
        self.assertEqual(2, len(availability_resp_obj.room_rates[0].line_items))

        booking_request = GoogleBookingSubmitRequest(
            api_version=1,
            transaction_id="booking-foo",
            hotel_id="700073765",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 1),
            language="en",
            customer=Customer(
                first_name="John",
                last_name="Bog",
                phone_number="555-867-5309",
                email="johnbog@simplenight.com",
                country="US",
            ),
            traveler=GoogleTraveler(first_name="John", last_name="Bog", occupancy=RoomParty(children=[10], adults=1)),
            room_rate=GoogleBookingRoomRate(
                code=availability_resp_obj.room_rates[0].code,
                room_type_code=availability_resp_obj.room_rates[0].room_type_code,
                rate_plan_code=availability_resp_obj.room_rates[0].rate_plan_code,
                maximum_allowed_occupancy=availability_resp_obj.room_rates[0].maximum_allowed_occupancy,
                total_price_at_booking=availability_resp_obj.room_rates[0].total_price_at_booking,
                total_price_at_checkout=availability_resp_obj.room_rates[0].total_price_at_checkout,
                partner_data=availability_resp_obj.room_rates[0].partner_data,
                line_items=availability_resp_obj.room_rates[0].line_items,
            ),
            payment=GooglePayment(
                type=PaymentMethod.PAYMENT_CARD,
                billing_address=Address(
                    city="San Francisco", province="CA", country="US", address1="123 Market Street", postal_code="94111"
                ),
                payment_card_parameters=GooglePaymentCardParameters(
                    card_type=CardType.VI,
                    card_number="4242424242424242",
                    cardholder_name="John Bog",
                    expiration_year="2025",
                    expiration_month="05",
                    cvc="123",
                ),
            ),
        )

        # Reset test request context.  This is necessary since using self.client in the same
        # test resets the request context, clearing its state at the end of the request
        # Could potentially use some more thought
        self.mock_request()

        priceline_contract_response = load_test_resource("priceline/bog1-contract-response.json")
        priceline_booking_response = load_test_resource("priceline/bog1-booking-response.json")
        booking_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_BOOK)
        contract_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_CONTRACT)
        with patch("stripe.Token.create") as stripe_token_mock:
            stripe_token_mock.return_value = {"id": "tok_foo"}

            with patch("stripe.Charge.create") as stripe_create_mock:
                stripe_create_mock.return_value = {
                    "currency": "USD",
                    "id": "payment-id",
                    "amount": 100.00,
                    "object": "settled",
                }

                with requests_mock.Mocker() as mocker:
                    mocker.post(booking_endpoint, text=priceline_booking_response)
                    mocker.post(contract_endpoint, text=priceline_contract_response)
                    response = self._post(endpoint=BOG_BOOKING, data=booking_request)

        booking_resp_obj = GoogleBookingResponse.parse_raw(response.content)
        self.assertIsNotNone(booking_resp_obj)
        self.assertEqual("booking-foo", booking_resp_obj.transaction_id)
        self.assertEqual(GoogleStatus.SUCCESS, booking_resp_obj.status)
        self.assertEqual("28954561478", booking_resp_obj.reservation.hotel_locators[0].id)
        self.assertEqual("700073765", booking_resp_obj.reservation.hotel_id)
        self.assertEqual("2020-11-11", str(booking_resp_obj.reservation.start_date))
        self.assertEqual("2020-11-16", str(booking_resp_obj.reservation.end_date))
        self.assertEqual("John", booking_resp_obj.reservation.customer.first_name)
        self.assertEqual("Bog", booking_resp_obj.reservation.customer.last_name)

        saved_booking = Booking.objects.get(transaction_id=booking_resp_obj.transaction_id)
        self.assertIsNotNone(saved_booking)
        self.assertEqual("2020-01-01", str(saved_booking.booking_date.date()))

    def _post(self, endpoint, data):
        return self.client.post(path=endpoint, data=data.json(), format="json")
