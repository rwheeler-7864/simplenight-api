from datetime import datetime, timedelta
from decimal import Decimal

import requests_mock

from api.activities import activity_service
from api.activities.adapters.tourcms.tourcms_transport import TourCmsTransport
from api.models.models import Feature
from api.multi.multi_product_models import ActivityLocationSearch
from api.tests import model_helper
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.tests.utils import load_test_resource


class TestTourCmsIntegration(SimplenightTestCase):
    @classmethod
    def setUpTestData(cls):
        latitude = Decimal("37.774930")
        longitude = Decimal("-122.419420")

        city = model_helper.create_geoname("123", "SF", "CA", "US", latitude=latitude, longitude=longitude)
        model_helper.create_geoname_altname(-1, city, "en", "Frisco")

    def setUp(self) -> None:
        super().setUp()
        self.stub_feature(Feature.ENABLED_ADAPTERS, "tourcms")

    def test_search_by_location(self):
        begin_date = datetime.now() + timedelta(days=30)
        end_date = datetime.now() + timedelta(days=37)
        search = ActivityLocationSearch(
            begin_date=begin_date.date(), end_date=end_date, adults=1, children=0, location_id="123"
        )

        transport = TourCmsTransport(test_mode=True)
        endpoint = transport.get_endpoint(TourCmsTransport.Endpoint.SEARCH)
        resource = load_test_resource("tourcms/tourcms_availability.json")
        with requests_mock.Mocker() as mocker:
            mocker.post(endpoint, text=resource)
            results = activity_service.search_by_location(search)

        print(results)
