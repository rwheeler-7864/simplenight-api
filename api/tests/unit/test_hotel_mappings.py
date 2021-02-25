from django.test import TestCase

from api.hotel import hotel_mappings
from api.models.models import ProviderMapping
from api.tests import model_helper


class TestHotelMappings(TestCase):
    def test_find_provider_hotel_mapping_id(self):
        provider = model_helper.create_provider(provider_name="foo")
        model_helper.create_provider_hotel(provider, "123", "Hotel 123")
        model_helper.create_provider_hotel(provider, "234", "Hotel 234")
        model_helper.create_provider_hotel(provider, "345", "Hotel 345")

        ProviderMapping(provider=provider, giata_code="SN_123", provider_code="123").save()
        ProviderMapping(provider=provider, giata_code="SN_345", provider_code="345").save()

        self.assertEqual("123", hotel_mappings.find_provider_hotel_id("SN_123", "foo"))
        self.assertEqual("345", hotel_mappings.find_provider_hotel_id("SN_345", "foo"))
        self.assertIsNone(hotel_mappings.find_provider_hotel_id("SN_234", "foo"))

    def test_find_provider_hotel(self):
        provider = model_helper.create_provider(provider_name="foo")
        model_helper.create_provider_hotel(provider, "123", "Hotel 123")
        model_helper.create_provider_hotel(provider, "234", "Hotel 234")
        model_helper.create_provider_hotel(provider, "345", "Hotel 345")

        ProviderMapping(provider=provider, giata_code="SN_123", provider_code="123").save()
        ProviderMapping(provider=provider, giata_code="SN_345", provider_code="345").save()

        self.assertEqual("Hotel 123", hotel_mappings.find_provider_hotel("SN_123", "foo").hotel_name)
        self.assertEqual("Hotel 345", hotel_mappings.find_provider_hotel("SN_345", "foo").hotel_name)
        self.assertIsNone(hotel_mappings.find_provider_hotel_id("SN_234", "foo"))

    def test_provider_to_simplenight_map(self):
        provider = model_helper.create_provider(provider_name="foo")
        model_helper.create_provider_hotel(provider, "123", "Hotel 123")
        model_helper.create_provider_hotel(provider, "234", "Hotel 234")
        model_helper.create_provider_hotel(provider, "345", "Hotel 345")

        ProviderMapping(provider=provider, giata_code="SN_123", provider_code="123").save()
        ProviderMapping(provider=provider, giata_code="SN_345", provider_code="345").save()

        simplenight_to_provider_map = hotel_mappings.find_provider_to_simplenight_map(
            provider_name="foo", provider_codes=["123", "345"]
        )

        self.assertEqual(2, len(simplenight_to_provider_map))
        self.assertEqual("SN_123", simplenight_to_provider_map["123"])
        self.assertEqual("SN_345", simplenight_to_provider_map["345"])

    def test_simplenight_to_provider_map(self):
        provider = model_helper.create_provider(provider_name="foo")
        model_helper.create_provider_hotel(provider, "123", "Hotel 123")
        model_helper.create_provider_hotel(provider, "234", "Hotel 234")
        model_helper.create_provider_hotel(provider, "345", "Hotel 345")

        ProviderMapping(provider=provider, giata_code="SN_123", provider_code="123").save()
        ProviderMapping(provider=provider, giata_code="SN_345", provider_code="345").save()

        simplenight_to_provider_map = hotel_mappings.find_simplenight_to_provider_map(
            provider_name="foo", giata_codes=["SN_123", "SN_345"]
        )

        self.assertEqual(2, len(simplenight_to_provider_map))
        self.assertEqual("123", simplenight_to_provider_map["SN_123"])
        self.assertEqual("345", simplenight_to_provider_map["SN_345"])
