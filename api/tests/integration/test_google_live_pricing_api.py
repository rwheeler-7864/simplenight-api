from datetime import date
from unittest.mock import patch

import requests_mock
from lxml import etree

from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.google_pricing import google_pricing_api
from api.hotel.google_pricing.google_pricing_models import GooglePricingItineraryQuery
from api.models.models import Feature, ProviderHotel, Provider
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.tests.utils import load_test_resource


class TestGoogleLivePricingHotelApi(SimplenightTestCase):
    def test_google_live_pricing(self):
        self.stub_feature(Feature.ENABLED_ADAPTERS, PricelineAdapter.get_provider_name())

        query = GooglePricingItineraryQuery(checkin=date(2020, 12, 20), nights=1, hotel_codes=["14479", "970041"])

        hotel_mappings = {
            "14479": "700243838",
            "970041": "702812247",
        }

        def mock_find_simplenight_hotel_id(provider_hotel_id, **_):
            mock_map = {
                "700243838": "14479",
                "702812247": "970041",
            }

            return mock_map.get(provider_hotel_id)

        provider = Provider.objects.get_or_create(name="giata")[0]
        ProviderHotel.objects.create(
            provider=provider,
            provider_code="14479",
            language_code="en",
            hotel_name="Hotel Foo",
            address_line_1="123 Foo Street",
            city_name="Fooville",
            state="FO",
            country_code="FO",
            latitude=100.0,
            longitude=50.0,
        )

        ProviderHotel.objects.create(
            provider=provider,
            provider_code="970041",
            language_code="en",
            hotel_name="Hotel Bar",
            address_line_1="123 Bar Street",
            city_name="Barville",
            state="BA",
            country_code="BA",
            latitude=100.0,
            longitude=50.0,
        )

        transport = PricelineTransport(test_mode=True)
        resource = load_test_resource("priceline/hotel-express-batch.json")
        endpoint = transport.endpoint(PricelineTransport.Endpoint.HOTEL_EXPRESS)

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id", mock_find_simplenight_hotel_id):
            with patch("api.hotel.hotel_mappings.find_simplenight_to_provider_map") as hotel_mappings_mock:
                with requests_mock.Mocker() as mocker:
                    mocker.get(endpoint, text=resource)
                    hotel_mappings_mock.return_value = hotel_mappings
                    result = google_pricing_api.live_pricing_api(query)

        self.assertIsNotNone(result)

        result_doc = etree.fromstring(result)
        self.assertEqual(2, len(result_doc.findall(".//Result")))
