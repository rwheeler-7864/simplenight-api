import asyncio
from datetime import timedelta, datetime, date
from decimal import Decimal
from typing import List

import requests_mock

from api.activities.activity_internal_models import AdapterActivityLocationSearch, AdapterActivity
from api.activities.adapters.tiqets.tiqets_activity_adapter import TiqetsActivityAdapter
from api.activities.adapters.tiqets.tiqets_transport import TiqetsTransport
from api.locations.models import LocationType, Location
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.tests.utils import load_test_resource


class TestTiqets(SimplenightTestCase):
    def test_search(self):
        location = Location(
            location_id="SF",
            language_code="en",
            location_name="San Francisco",
            iso_country_code="US",
            latitude=Decimal("37.774930"),
            longitude=Decimal("-122.419420"),
            location_type=LocationType.CITY,
        )

        begin_date = datetime.now() + timedelta(days=30)
        end_date = datetime.now() + timedelta(days=37)
        search = AdapterActivityLocationSearch(
            begin_date=begin_date.date(), end_date=end_date, adults=1, children=0, location=location
        )

        saved_search_response = load_test_resource("tiqets/tiqets-search-response.json")
        transport = TiqetsTransport(test_mode=True)
        adapter = TiqetsActivityAdapter(TiqetsTransport(test_mode=True))
        with requests_mock.Mocker() as mocker:
            mocker.post(transport.get_endpoint(TiqetsTransport.Endpoint.SEARCH), text=saved_search_response)
            results: List[AdapterActivity] = asyncio.run(adapter.search_by_location(search))

        self.assertEqual("974626", results[0].code)
        self.assertEqual("San Francisco Museum of Modern Art (SFMOMA)", results[0].name)
        self.assertIn("Not just one of the largest museums", results[0].description)
        self.assertEqual(Decimal("20.61"), results[0].total_price.amount)
        self.assertEqual("EUR", results[0].total_price.currency)
        self.assertEqual(["ATTRACTION"], results[0].categories)
        self.assertEqual(5, len(results[0].images))

    def test_details(self):
        adapter = TiqetsActivityAdapter(TiqetsTransport(test_mode=True))
        asyncio.run(adapter.details(product_id="974626", date_from=date(2020, 2, 10), date_to=date(2020, 2, 10)))
