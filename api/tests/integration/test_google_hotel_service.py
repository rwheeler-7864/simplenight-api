from datetime import datetime, timedelta
from unittest.mock import patch

import requests_mock
from freezegun import freeze_time

from api.hotel import google_hotel_service
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.converter.google_models import GoogleHotelSearchRequest, RoomParty
from api.models.models import Feature
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.tests.utils import load_test_resource


class TestGoogleHotelService(SimplenightTestCase):
    @freeze_time("2020-10-09")
    def test_line_item_calculations(self):
        self.stub_feature(Feature.ENABLED_ADAPTERS, "priceline")
        self.stub_feature(Feature.TEST_MODE, "true")

        hotel_id = "700033110"
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = GoogleHotelSearchRequest(
            api_version=1,
            transaction_id="foo",
            start_date=checkin,
            end_date=checkout,
            party=RoomParty(children=[], adults=1),
            hotel_id=hotel_id,
        )

        transport = PricelineTransport(test_mode=True)
        priceline_hotel_id_response = load_test_resource("priceline/priceline-postpaid-hotelavail.json")
        priceline_contract_response = load_test_resource("priceline/priceline-postpaid-contract1.json")
        avail_endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)
        contract_endpoint = transport.endpoint(PricelineTransport.Endpoint.EXPRESS_CONTRACT)

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            with patch("api.hotel.hotel_mappings.find_provider_hotel_id") as mock_find_provider:
                mock_find_provider.return_value = hotel_id
                with requests_mock.Mocker() as mocker:
                    mocker.get(avail_endpoint, text=priceline_hotel_id_response)
                    mocker.post(contract_endpoint, text=priceline_contract_response)

                    results = google_hotel_service.search_by_id(search)

        self.assertIsNotNone(results)
        self.assertIsNotNone(results.room_rates)

        room_rate = results.room_rates[0]

        line_item_total_booking = sum(x.price.amount for x in room_rate.line_items if not x.paid_at_checkout)
        line_item_total_checkout = sum(x.price.amount for x in room_rate.line_items if x.paid_at_checkout)

        self.assertEqual(room_rate.total_price_at_booking.amount, line_item_total_booking)
        self.assertEqual(room_rate.total_price_at_checkout.amount, line_item_total_checkout)
