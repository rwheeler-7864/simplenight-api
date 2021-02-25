from api.hotel.adapters import adapter_common
from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.models.models import CityMap
from api.tests import test_objects, model_helper
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestHotelAdapter(SimplenightTestCase):
    def test_get_provider_location(self):
        provider = model_helper.create_provider("priceline")
        provider.save()

        model_helper.create_geoname(1, "San Francisco", "CA", "US", population=100)
        model_helper.create_provider_city(provider.name, code="10", name="San Francisco", province="CA", country="US")
        CityMap.objects.create(simplenight_city_id=1, provider=provider, provider_city_id=10)

        priceline = PricelineAdapter.factory()
        search = test_objects.adapter_location_search(location_id=1)

        provider_location = priceline.get_provider_location(search)
        self.assertEqual("San Francisco", provider_location.location_name)
        self.assertEqual("10", provider_location.provider_code)
