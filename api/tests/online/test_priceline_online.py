from datetime import datetime, timedelta
from unittest.mock import patch

from api.hotel.models.hotel_common_models import RoomOccupancy
from api.hotel import hotel_service
from api.booking import booking_service
from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.models.hotel_api_model import HotelLocationSearch, HotelSpecificSearch
from api.hotel.models.adapter_models import (
    AdapterLocationSearch,
    AdapterOccupancy,
    AdapterHotelSearch,
    AdapterCancelRequest,
    AdapterHotelBatchSearch,
)
from api.hotel.parsers.priceline_details_parser import PricelineDetailsParser
from api.models.models import CityMap, HotelBooking
from api.tests import test_objects, model_helper
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestPricelineIntegration(SimplenightTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.provider = model_helper.create_provider("priceline")
        self.provider.save()

        model_helper.create_geoname(1, "San Francisco", "CA", "US", population=100)
        model_helper.create_provider_city(
            self.provider.name, code="800046992", name="San Francisco", province="CA", country="US"
        )

        CityMap.objects.create(simplenight_city_id=1, provider=self.provider, provider_city_id=800046992)

    def test_transport_test_mode(self):
        transport = PricelineTransport(test_mode=True)
        hotel_express_url = transport.endpoint(transport.Endpoint.HOTEL_EXPRESS)
        self.assertEqual("https://api-sandbox.rezserver.com/api/hotel/getExpress.Results", hotel_express_url)

        transport = PricelineTransport(test_mode=False)
        hotel_express_url = transport.endpoint(transport.Endpoint.HOTEL_EXPRESS)
        self.assertEqual("https://api.rezserver.com/api/hotel/getExpress.Results", hotel_express_url)

    def test_hotel_express_city_availability(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        location = "1"
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        occupancy = AdapterOccupancy()
        search_request = AdapterLocationSearch(
            start_date=checkin, end_date=checkout, occupancy=occupancy, location_id=location
        )

        results = priceline.search_by_location(search_request)
        self.assertIsNotNone(results)
        self.assertTrue(len(results) > 1)

    def test_hotel_express_hotel_availability(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        hotel_id = "700363264"
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = AdapterHotelSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=AdapterOccupancy(),
            provider_hotel_id=hotel_id,
            simplenight_hotel_id="SN123",
        )

        results = priceline.search_by_id(search)
        self.assertIsNotNone(results)
        self.assertEqual("700363264", results.hotel_id)
        self.assertEqual("Best Western Plus Bayside Hotel", results.hotel_details.name)

    def test_search_by_hotel_id_batch(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        hotel_ids = ["700363264", "702812247", "700243838"]
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = AdapterHotelBatchSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=AdapterOccupancy(),
            provider_hotel_ids=hotel_ids,
            simplenight_hotel_ids=["SN123", "SN456", "SN789"],
        )

        results = priceline.search_by_id_batch(search)
        self.assertIsNotNone(results)
        self.assertEqual(3, len(results))

        results.sort(key=lambda x: hotel_ids.index(x.hotel_id))
        self.assertEqual("700363264", results[0].hotel_id)
        self.assertEqual("Best Western Plus Bayside Hotel", results[0].hotel_details.name)

        self.assertEqual("702812247", results[1].hotel_id)
        self.assertEqual("Hyatt Place San Francisco/Downtown", results[1].hotel_details.name)

        self.assertEqual("700243838", results[2].hotel_id)
        self.assertEqual("Hyatt Centric Fisherman's Wharf San Francisco", results[2].hotel_details.name)

    def test_recheck_room_rate(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        hotel_id = "700363264"
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = AdapterHotelSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=AdapterOccupancy(),
            provider_hotel_id=hotel_id,
            simplenight_hotel_id="SN123",
        )

        results = priceline.search_by_id(search)
        self.assertTrue(len(results.room_rates) >= 1)

        verified_rate = priceline.recheck(results.room_rates[0])
        self.assertIsNotNone(verified_rate)
        self.assertIsNotNone(verified_rate.code)

        print(results)

    def test_booking(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        occupancy = AdapterOccupancy()
        search = AdapterLocationSearch(start_date=checkin, end_date=checkout, occupancy=occupancy, location_id="1")

        availability_response = priceline.search_by_location(search)
        hotel = availability_response[0]

        payment_object = test_objects.payment("4111111111111111")

        room_rate_to_book = priceline.recheck(hotel.room_rates[0])
        booking_request = test_objects.booking_request(payment_object, rate_code=room_rate_to_book.code)

        booking_request.customer.first_name = "James"
        booking_request.customer.last_name = "Morton"
        booking_request.customer.email = "jmorton@simplenight.com"

        reservation = priceline.book(booking_request)

        print(reservation)
        self.assertIsNotNone(reservation.locator)

    def test_priceline_booking_service(self):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = HotelLocationSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=1),
            location_id="1",
            provider="priceline",
        )

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            availability_response = hotel_service.search_by_location(search)

        self.assertTrue(len(availability_response) >= 1)
        self.assertTrue(len(availability_response[0].room_types) >= 1)

        hotel_to_book = availability_response[0]
        room_to_book = hotel_to_book.room_types[0]
        booking_request = test_objects.booking_request(rate_code=room_to_book.code)
        booking_response = booking_service.book_hotel(booking_request)

        self.assertIsNotNone(booking_response.transaction_id)
        self.assertIsNotNone(booking_response.booking_id)
        self.assertTrue(booking_response.status.success)
        self.assertIsNotNone(booking_response.reservation.locator.id)
        self.assertEqual("John", booking_response.reservation.customer.first_name)
        self.assertEqual("Simplenight", booking_response.reservation.customer.last_name)

    def test_priceline_cancel(self):
        transport = PricelineTransport(test_mode=True)
        adapter = PricelineAdapter(transport=transport)

        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=31)
        search = HotelSpecificSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=1),
            hotel_id="14479",
            provider="priceline",
        )

        with patch("api.hotel.hotel_mappings.find_provider_hotel_id") as mock_find_provider_hotel_id:
            mock_find_provider_hotel_id.return_value = "700243838"
            with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
                mock_find_simplenight_id.return_value = "14779"
                availability_response = hotel_service.search_by_id(search)

        self.assertIsNotNone(availability_response)
        room_to_book = availability_response.room_types[0]
        booking_request = test_objects.booking_request(rate_code=room_to_book.code)
        booking_response = booking_service.book_hotel(booking_request)

        hotel_booking = HotelBooking.objects.get(booking__recordlocator__record_locator=booking_response.booking_id)

        cancel_response = adapter.cancel(
            AdapterCancelRequest(
                hotel_id=hotel_booking.provider_hotel_id,
                record_locator=hotel_booking.record_locator,
                email_address=booking_request.customer.email,
            )
        )

        self.assertTrue(cancel_response.is_cancelled)

    def test_download_policies(self):
        transport = PricelineTransport(test_mode=False)
        results = transport.policies_download(site_refid=2050)
        print(results)

    def test_priceline_details_parser(self):
        transport = PricelineTransport(test_mode=True)
        parser = PricelineDetailsParser(transport)
        parser.load(chunk_size=10, limit=10)

    def test_priceline_reviews(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport=transport)
        print(priceline.reviews(hotel_id="700363264"))
