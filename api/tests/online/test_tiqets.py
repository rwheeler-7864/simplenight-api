import asyncio
from datetime import datetime, timedelta, date
from decimal import Decimal

from api.activities.activity_internal_models import AdapterActivityLocationSearch
from api.activities.adapters.tiqets.tiqets_activity_adapter import TiqetsActivityAdapter
from api.activities.adapters.tiqets.tiqets_transport import TiqetsTransport
from api.locations.models import Location, LocationType
from api.tests.unit.simplenight_test_case import SimplenightTestCase


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

        adapter = TiqetsActivityAdapter(TiqetsTransport(test_mode=True))
        print(asyncio.run(adapter.search_by_location(search)))

    def test_details(self):
        adapter = TiqetsActivityAdapter(TiqetsTransport(test_mode=True))
        asyncio.run(adapter.details(product_id="974626", date_from=date(2020, 2, 10), date_to=date(2020, 2, 10)))
