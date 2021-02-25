import pytest

from api.hotel.adapters import adapter_service
from api.models.models import Feature
from api.tests import test_objects
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.view.exceptions import AvailabilityException


class TestAdapterService(SimplenightTestCase):
    def test_get_adapters_to_search(self):
        search = test_objects.hotel_specific_search(provider="priceline")
        adapter = adapter_service.get_hotel_adapters_to_search(search)[0]
        self.assertEqual("priceline", adapter.get_provider_name())

        self.stub_feature(Feature.ENABLED_ADAPTERS, "hotelbeds")

        search.provider = None
        adapter = adapter_service.get_hotel_adapters_to_search(search)[0]
        self.assertEqual("hotelbeds", adapter.get_provider_name())

        # With no adapters set on the search, or organization, fall back to "stub_hotel"
        self.clear_feature(Feature.ENABLED_ADAPTERS)
        adapter = adapter_service.get_hotel_adapters_to_search(search)[0]
        self.assertEqual("stub_hotel", adapter.get_provider_name())

    def test_get_unknown_adapter(self):
        search = test_objects.hotel_specific_search(provider="UNKNOWN-PROVIDER")
        with pytest.raises(AvailabilityException):
            adapter_service.get_hotel_adapters_to_search(search)

    def test_get_test_mode(self):
        self.assertTrue(adapter_service.get_test_mode())  # Default to True

        self.stub_feature(Feature.TEST_MODE, "false")
        self.assertFalse(adapter_service.get_test_mode())

        self.stub_feature(Feature.TEST_MODE, "true")
        self.assertTrue(adapter_service.get_test_mode())

        self.stub_feature(Feature.TEST_MODE, "false")
        self.assertFalse(adapter_service.get_test_mode())
