import uuid
from datetime import timedelta, datetime, date
from decimal import Decimal
from unittest.mock import patch

import pytest
import requests_mock
from freezegun import freeze_time

from api.hotel import hotel_service
from api.booking import booking_service
from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.models.adapter_models import (
    AdapterHotelSearch,
    AdapterOccupancy,
    AdapterLocationSearch,
    AdapterCancelRequest,
    AdapterHotelBatchSearch,
)
from api.hotel.models.booking_model import HotelBookingRequest, PaymentMethod, Payment
from api.hotel.models.hotel_api_model import HotelLocationSearch, HotelSpecificSearch, CancellationSummary
from api.hotel.models.hotel_common_models import RoomOccupancy, RateType
from api.models.models import CityMap, Booking, HotelCancellationPolicy
from api.tests import test_objects, model_helper
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.tests.utils import load_test_resource
from api.view.exceptions import BookingException


class TestPricelineUnit(SimplenightTestCase):
    def setUp(self) -> None:
        super().setUp()
        provider = model_helper.create_provider("priceline")
        provider.save()

        model_helper.create_geoname(1, "San Francisco", "CA", "US", population=100)
        model_helper.create_provider_city(
            provider.name, code="800046992", name="San Francisco", province="CA", country="US"
        )

        CityMap.objects.create(simplenight_city_id=1, provider=provider, provider_city_id=800046992)

    def test_hotel_express_hotel_search(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        hotel_id = "700363264"
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        occupancy = AdapterOccupancy()
        search = AdapterHotelSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=occupancy,
            provider_hotel_id=hotel_id,
            simplenight_hotel_id="SN123",
        )

        # Null mandatory fees
        priceline_contract_response = load_test_resource("priceline/priceline-postpaid-contract2.json")
        priceline_hotel_id_response = load_test_resource("priceline/hotel_specific_search_response.json")

        avail_endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)
        contract_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_CONTRACT)
        with requests_mock.Mocker() as mocker:
            mocker.get(avail_endpoint, text=priceline_hotel_id_response)
            mocker.post(contract_endpoint, text=priceline_contract_response)
            results = priceline.search_by_id(search)

        self.assertEqual("priceline", results.provider)
        self.assertEqual("700363264", results.hotel_id)
        self.assertIsNotNone(results.start_date)
        self.assertIsNotNone(results.end_date)
        self.assertEqual(1, results.occupancy.adults)

        self.assertEqual("Best Western Plus Bayside Hotel", results.hotel_details.name)
        self.assertEqual("Best Western International", results.hotel_details.chain_name)
        self.assertEqual("1717 Embarcadero", results.hotel_details.address.address1)
        self.assertEqual("Oakland", results.hotel_details.address.city)
        self.assertEqual("CA", results.hotel_details.address.province)
        self.assertEqual("US", results.hotel_details.address.country)
        self.assertEqual("CA 94606", results.hotel_details.address.postal_code)
        self.assertIn("This bay front Oakland hotel", results.hotel_details.property_description)
        self.assertEqual(10.0, results.hotel_details.review_rating)
        self.assertEqual(3.0, results.hotel_details.star_rating)

        self.assertAlmostEqual(701.70, float(results.room_rates[0].total_base_rate.amount))
        self.assertEqual("USD", results.room_rates[0].total_base_rate.currency)

    @freeze_time("2020-10-01")
    def test_hotel_express_location_search(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        location = "1"
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search_request = AdapterLocationSearch(
            start_date=checkin, end_date=checkout, occupancy=AdapterOccupancy(), location_id=location
        )

        resource_file = "priceline/priceline-hotel-express-city-cancellable-rates.json"
        priceline_city_search_resource = load_test_resource(resource_file)

        endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)
        with requests_mock.Mocker() as mocker:
            mocker.get(endpoint, text=priceline_city_search_resource)
            results = priceline.search_by_location(search_request)

        self.assertEqual(10, len(results))
        self.assertEqual("St. Regis San Francisco", results[0].hotel_details.name)
        self.assertEqual("The Mosser Hotel", results[1].hotel_details.name)
        self.assertEqual(CancellationSummary.NON_REFUNDABLE, results[0].rate_plans[0].cancellation_policy.summary)
        self.assertEqual(CancellationSummary.FREE_CANCELLATION, results[1].rate_plans[0].cancellation_policy.summary)

    def test_priceline_booking(self):
        booking_request = test_objects.booking_request()
        priceline_booking_response = load_test_resource("priceline/booking-response.json")

        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport=PricelineTransport(test_mode=True))
        endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_BOOK)

        with requests_mock.Mocker() as mocker:
            mocker.post(endpoint, text=priceline_booking_response)
            reservation = priceline.book(booking_request)

        self.assertEqual("30796806215", reservation.locator.id)
        self.assertEqual("CONF0", reservation.hotel_locator[0].id)
        self.assertIsNotNone(reservation.checkin)
        self.assertIsNotNone(reservation.checkout)
        self.assertEqual(1, reservation.traveler.occupancy.adults)
        self.assertEqual("John", reservation.traveler.first_name)
        self.assertEqual("Simplenight", reservation.traveler.last_name)
        self.assertEqual(RateType.BOOKABLE, reservation.room_rate.rate_type)

    @freeze_time("2020-10-01")
    def test_priceline_booking_service_cancellation_policies(self):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = HotelLocationSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=1),
            location_id="1",
            provider="priceline",
        )

        resource_file = "priceline/priceline-hotel-express-city-cancellable-rates.json"
        priceline_city_search_resource = load_test_resource(resource_file)
        priceline_booking_response = load_test_resource("priceline/booking-response-cancellable.json")
        priceline_recheck_response = load_test_resource("priceline/recheck-response.json")

        transport = PricelineTransport(test_mode=True)
        avail_endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)
        book_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_BOOK)
        recheck_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_CONTRACT)

        with patch("stripe.Token.create") as stripe_token_mock:
            stripe_token_mock.return_value = {"id": "tok_foo"}

            with patch("stripe.Charge.create") as stripe_create_mock:
                stripe_create_mock.return_value = {
                    "currency": "USD",
                    "id": "payment-id",
                    "amount": 100.00,
                    "object": "settled",
                }
                with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
                    mock_find_simplenight_id.return_value = "123"
                    with requests_mock.Mocker() as mocker:
                        mocker.get(avail_endpoint, text=priceline_city_search_resource)
                        mocker.post(recheck_endpoint, text=priceline_recheck_response)
                        mocker.post(book_endpoint, text=priceline_booking_response)
                        availability_response = hotel_service.search_by_location(search)

                        self.assertTrue(len(availability_response) >= 1)
                        self.assertTrue(len(availability_response[0].room_types) >= 1)

                        hotel_to_book = availability_response[0]
                        room_to_book = hotel_to_book.room_types[0]
                        booking_request = test_objects.booking_request(rate_code=room_to_book.code)

                        booking_response = booking_service.book_hotel(booking_request)

        booking = Booking.objects.get(transaction_id=booking_response.transaction_id)
        booking_id = booking.booking_id
        cancellation_policies = HotelCancellationPolicy.objects.filter(hotel_booking__booking__booking_id=booking_id)

        self.assertEqual(3, len(cancellation_policies))
        self.assertEqual("FREE_CANCELLATION", cancellation_policies[0].cancellation_type)
        self.assertEqual("2017-02-03", str(cancellation_policies[0].begin_date))
        self.assertEqual("2020-10-29", str(cancellation_policies[0].end_date))

        self.assertEqual("PARTIAL_REFUND", cancellation_policies[1].cancellation_type)
        self.assertEqual("2020-10-29", str(cancellation_policies[1].begin_date))
        self.assertEqual("2020-10-31", str(cancellation_policies[1].end_date))

        self.assertEqual("NON_REFUNDABLE", cancellation_policies[2].cancellation_type)
        self.assertEqual("2020-10-31", str(cancellation_policies[2].begin_date))
        self.assertEqual("2024-07-27", str(cancellation_policies[2].end_date))

    @freeze_time("2020-10-09")
    def test_priceline_postpaid_fees(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        hotel_id = "700033110"
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = AdapterHotelSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=AdapterOccupancy(),
            provider_hotel_id=hotel_id,
            simplenight_hotel_id="SN123",
        )

        priceline_hotel_id_response = load_test_resource("priceline/priceline-postpaid-hotelavail.json")
        priceline_contract_response = load_test_resource("priceline/priceline-postpaid-contract1.json")
        avail_endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)
        contract_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_CONTRACT)
        with requests_mock.Mocker() as mocker:
            mocker.get(avail_endpoint, text=priceline_hotel_id_response)
            mocker.post(contract_endpoint, text=priceline_contract_response)
            results = priceline.search_by_id(search)

        self.assertEqual(Decimal("233.20"), results.room_rates[0].postpaid_fees.total.amount)
        self.assertEqual("USD", results.room_rates[0].postpaid_fees.total.currency)
        self.assertEqual(1, len(results.room_rates[0].postpaid_fees.fees))
        self.assertEqual("Resort Fee", results.room_rates[0].postpaid_fees.fees[0].description)

    @freeze_time("2020-10-12")
    def test_multi_room(self):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=31)
        search = HotelSpecificSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=2, num_rooms=1),
            hotel_id="700021105",
            provider="priceline",
        )

        transport = PricelineTransport(test_mode=True)
        avail_endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)

        single_room_response = load_test_resource("priceline/priceline-multiroom-numroom1.json")
        multi_room_response = load_test_resource("priceline/priceline-multiroom-numroom2.json")

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            with patch("api.hotel.hotel_mappings.find_provider_hotel_id") as mock_find_provider:
                mock_find_provider.return_value = "ABC123"
                with requests_mock.Mocker() as mocker:
                    mocker.get(avail_endpoint, text=single_room_response)
                    availability_response = hotel_service.search_by_id(search)

        self.assertEqual(1, availability_response.occupancy.num_rooms)
        self.assertEqual(Decimal("230.88"), availability_response.room_types[0].total.amount)
        self.assertEqual(Decimal("189.28"), availability_response.room_types[0].total_base_rate.amount)

        search.occupancy.num_rooms = 2

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            with patch("api.hotel.hotel_mappings.find_provider_hotel_id") as mock_find_provider:
                mock_find_provider.return_value = "ABC123"
                with requests_mock.Mocker() as mocker:
                    mocker.get(avail_endpoint, text=multi_room_response)
                    availability_response = hotel_service.search_by_id(search)

        self.assertEqual(2, availability_response.occupancy.num_rooms)
        self.assertEqual(Decimal("455.04"), availability_response.room_types[0].total.amount)
        self.assertEqual(Decimal("378.56"), availability_response.room_types[0].total_base_rate.amount)

    def test_priceline_cancel(self):
        transport = PricelineTransport(test_mode=True)
        adapter = PricelineAdapter(transport=transport)

        lookup_resource = load_test_resource("priceline/priceline-lookup-response.json")
        lookup_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_LOOKUP)
        cancel_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_CANCEL)
        cancel_resource = load_test_resource("priceline/priceline-cancel-response.json")
        with requests_mock.Mocker() as mocker:
            mocker.post(lookup_endpoint, text=lookup_resource)
            mocker.post(cancel_endpoint, text=cancel_resource)

            cancel_response = adapter.cancel(
                AdapterCancelRequest(hotel_id="14479", record_locator="700243838", email_address="foo@bar.baz")
            )

        self.assertTrue(cancel_response.is_cancelled)

    def test_priceline_cancel_failure(self):
        transport = PricelineTransport(test_mode=True)
        adapter = PricelineAdapter(transport=transport)

        lookup_resource = load_test_resource("priceline/priceline-lookup-response.json")
        lookup_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_LOOKUP)
        cancel_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_CANCEL)
        cancel_resource = load_test_resource("priceline/priceline-cancel-failure-response.json")
        with requests_mock.Mocker() as mocker:
            mocker.post(lookup_endpoint, text=lookup_resource)
            mocker.post(cancel_endpoint, text=cancel_resource)

            with pytest.raises(BookingException) as e:
                adapter.cancel(
                    AdapterCancelRequest(hotel_id="14479", record_locator="700243838", email_address="foo@bar.baz")
                )

        self.assertIn("Could not cancel booking", str(e))

    def test_priceline_booking_error_handled(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport)

        payment_object = test_objects.payment("4111111111111111")
        booking_request = test_objects.booking_request(payment_object)

        mock_priceline_booking_response = load_test_resource("priceline/priceline-book-error.json")
        booking_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_BOOK)
        with requests_mock.Mocker() as mocker:
            mocker.post(booking_endpoint, text=mock_priceline_booking_response)
            with pytest.raises(BookingException) as e:
                priceline.book(booking_request)

        self.assertEqual("Hotel.Express.Book: Invalid name_first", str(e.value))

    def test_priceline_search_by_hotel_id_batch(self):
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

        resource = load_test_resource("priceline/hotel-express-batch.json")
        endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)
        with requests_mock.Mocker() as mocker:
            mocker.get(endpoint, text=resource)
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

    @freeze_time("2020-10-01")
    def test_priceline_booking_service_no_billing_address(self):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = HotelLocationSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=1),
            location_id="1",
            provider="priceline",
        )

        resource_file = "priceline/priceline-hotel-express-city-cancellable-rates.json"
        priceline_city_search_resource = load_test_resource(resource_file)
        priceline_booking_response = load_test_resource("priceline/booking-response-cancellable.json")
        priceline_recheck_response = load_test_resource("priceline/recheck-response.json")

        transport = PricelineTransport(test_mode=True)
        avail_endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)
        book_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_BOOK)
        recheck_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_CONTRACT)

        with patch("stripe.Token.create") as stripe_token_mock:
            stripe_token_mock.return_value = {"id": "tok_foo"}

            with patch("stripe.Charge.create") as stripe_create_mock:
                stripe_create_mock.return_value = {
                    "currency": "USD",
                    "id": "payment-id",
                    "amount": 100.00,
                    "object": "settled",
                }
                with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
                    mock_find_simplenight_id.return_value = "123"
                    with requests_mock.Mocker() as mocker:
                        mocker.get(avail_endpoint, text=priceline_city_search_resource)
                        mocker.post(recheck_endpoint, text=priceline_recheck_response)
                        mocker.post(book_endpoint, text=priceline_booking_response)
                        availability_response = hotel_service.search_by_location(search)

                        self.assertTrue(len(availability_response) >= 1)
                        self.assertTrue(len(availability_response[0].room_types) >= 1)

                        hotel_to_book = availability_response[0]
                        room_to_book = hotel_to_book.room_types[0]

                        payment = Payment(payment_method=PaymentMethod.PAYMENT_TOKEN, payment_token="tok_mastercard")

                        booking_request = HotelBookingRequest(
                            api_version=1,
                            transaction_id=str(uuid.uuid4())[:8],
                            hotel_id="1",
                            language="en_US",
                            customer=test_objects.customer(),
                            traveler=test_objects.traveler(),
                            room_code=room_to_book.code,
                            payment=payment,
                        )

                        booking_response = booking_service.book_hotel(booking_request)

        print(booking_response)

    def test_priceline_reviews(self):
        transport = PricelineTransport(test_mode=True)
        priceline = PricelineAdapter(transport=transport)

        priceline_reviews_resource = load_test_resource("priceline/priceline-user-reviews.json")
        with requests_mock.Mocker() as mocker:
            mocker.get(transport.endpoint(PricelineTransport.Endpoint.REVIEWS), text=priceline_reviews_resource)
            reviews = priceline.reviews(hotel_id="700363264")

        self.assertEqual(9.4, reviews.average_rating)
        self.assertEqual(5, reviews.review_count)
        self.assertEqual(5, len(reviews.reviews))
        self.assertEqual("Gregory", reviews.reviews[0].reviewer_name)
        self.assertEqual(date(2020, 9, 2), reviews.reviews[0].review_date)
        self.assertEqual(10.0, reviews.reviews[0].review_rating)
        self.assertIn("Big clean room", reviews.reviews[0].good_text)
        self.assertIn("They charge 15 bucks for parking", reviews.reviews[0].bad_text)
