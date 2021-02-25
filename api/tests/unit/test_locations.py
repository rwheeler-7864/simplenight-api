from decimal import Decimal

from django.test import TestCase

from api.locations import location_service
from api.locations.models import LocationType
from api.models.models import CityMap
from api.tests import model_helper


class TestLocationService(TestCase):
    def setUp(self) -> None:
        super().setUp()
        geoname_sfo = model_helper.create_geoname(1, "San Francisco", "CA", "US", population=100)
        geoname_sea = model_helper.create_geoname(2, "Seattle", "WA", "US", population=5000)
        geoname_nyc = model_helper.create_geoname(3, "New York", "NY", "US", population=10000)
        geoname_san = model_helper.create_geoname(4, "San Diego", "CA", "US", population=50)
        geoname_sat = model_helper.create_geoname(5, "San Antonio", "TX", "US", population=500)

        geoname_lon = model_helper.create_geoname(6, "London", "LON", "UK", population=200)
        geoname_man = model_helper.create_geoname(7, "Manchester", "MAN", "UK", population=500)

        geoname_lax = model_helper.create_geoname(8, "Los Angeles", "LAX", "US", population=5000)

        model_helper.create_geoname_altname(1, geoname_sfo, "en", "San Francisco")
        model_helper.create_geoname_altname(1, geoname_sfo, "jp", "サンフランシスコ")
        model_helper.create_geoname_altname(2, geoname_sea, "en", "Seattle")
        model_helper.create_geoname_altname(3, geoname_nyc, "en", "New York City")
        model_helper.create_geoname_altname(4, geoname_san, "en", "San Diego")
        model_helper.create_geoname_altname(5, geoname_sat, "en", "San Antonio")

        model_helper.create_geoname_altname(6, geoname_lon, "en", "London")
        model_helper.create_geoname_altname(7, geoname_man, "en", "Manchester")

        model_helper.create_geoname_altname(8, geoname_lax, "en", "LA")
        model_helper.create_geoname_altname(8, geoname_lax, "en", "Los Angeles2")
        model_helper.create_geoname_altname(8, geoname_lax, "en", "Los Angeles", is_preferred=True)
        model_helper.create_geoname_altname(8, geoname_lax, "en", "Los Angel")
        model_helper.create_geoname_altname(8, geoname_lax, "en", "Los Ang")

    def test_find_by_prefix(self):
        cities = location_service.find_by_prefix("San ")
        self.assertEqual(3, len(cities))

        self.assertEqual("5", cities[0].location_id)
        self.assertEqual("San Antonio", cities[0].location_name)
        self.assertEqual("TX", cities[0].province)
        self.assertEqual("US", cities[0].iso_country_code)
        self.assertEqual("en", cities[0].language_code)
        self.assertEqual(Decimal("50.000000"), cities[0].latitude)
        self.assertEqual(Decimal("50.000000"), cities[0].longitude)
        self.assertEqual(LocationType.CITY, cities[0].location_type)

        self.assertEqual("1", cities[1].location_id)
        self.assertEqual("San Francisco", cities[1].location_name)
        self.assertEqual("CA", cities[1].province)
        self.assertEqual("US", cities[1].iso_country_code)
        self.assertEqual("en", cities[1].language_code)
        self.assertEqual(Decimal("50.000000"), cities[1].latitude)
        self.assertEqual(Decimal("50.000000"), cities[1].longitude)
        self.assertEqual(LocationType.CITY, cities[1].location_type)

        self.assertEqual("4", cities[2].location_id)
        self.assertEqual("San Diego", cities[2].location_name)
        self.assertEqual("en", cities[2].language_code)
        self.assertEqual("CA", cities[2].province)
        self.assertEqual("US", cities[2].iso_country_code)
        self.assertEqual(Decimal("50.000000"), cities[2].latitude)
        self.assertEqual(Decimal("50.000000"), cities[2].longitude)
        self.assertEqual(LocationType.CITY, cities[2].location_type)

        cities = location_service.find_by_prefix("No Match")
        self.assertEqual(0, len(cities))

        # noinspection PyTypeChecker
        cities = location_service.find_by_prefix(None)
        self.assertEqual(0, len(cities))

    def test_find_by_prefix_alt_language(self):
        cities = location_service.find_by_prefix("サンフラ", language_code="jp")
        self.assertEqual(1, len(cities))
        self.assertEqual("サンフランシスコ", cities[0].location_name)
        self.assertEqual("jp", cities[0].language_code)

    def test_find_by_geoname_id(self):
        cities = location_service.find_city_by_simplenight_id(1)
        self.assertEqual("1", cities.location_id)
        self.assertEqual("San Francisco", cities.location_name)
        self.assertEqual("CA", cities.province)
        self.assertEqual("US", cities.iso_country_code)
        self.assertEqual("en", cities.language_code)

    def test_find_by_geoname_id_alt_language(self):
        cities = location_service.find_city_by_simplenight_id(1, language_code="jp")
        self.assertEqual("1", cities.location_id)
        self.assertEqual("サンフランシスコ", cities.location_name)
        self.assertEqual("CA", cities.province)
        self.assertEqual("US", cities.iso_country_code)
        self.assertEqual("jp", cities.language_code)

    def find_all_locations(self):
        cities = location_service.find_all_cities()
        self.assertEqual(7, len(cities))

    def find_all_locations_in_country(self):
        cities = location_service.find_all_cities(country_code="UK")
        self.assertEqual(2, len(cities))

    def test_find_by_prefix_airports_included(self):
        model_helper.create_airport(airport_code="SFO", airport_name="San Francisco Intl", airport_id=1)
        model_helper.create_airport(airport_code="SAN", airport_name="San Diego Intl", airport_id=1)
        model_helper.create_airport(airport_code="OAK", airport_name="Oakland Airport", airport_id=2)
        model_helper.create_airport(airport_code="JFK", airport_name="John F. Kennedy International", airport_id=2)

        # Includes San Francisco Intl, matched by airport_name
        # Airport code exact match sorted to first entry, SAN = San Diego
        locations = location_service.find_by_prefix("San")
        self.assertEqual(5, len(locations))
        self.assertEqual("San Diego Intl", locations[0].location_name)
        self.assertEqual("San Francisco Intl", locations[4].location_name)

        # Includes San Francisco Intl, matched by airport_code
        locations = location_service.find_by_prefix("SFO")
        self.assertEqual(1, len(locations))
        self.assertEqual("San Francisco Intl", locations[0].location_name)
        self.assertEqual(LocationType.AIRPORT, locations[0].location_type)

    def test_find_provider_city(self):
        provider = model_helper.create_provider("priceline")
        provider.save()

        model_helper.create_provider_city(provider.name, code="10", name="San Francisco", province="CA", country="US")
        model_helper.create_provider_city(provider.name, code="20", name="Seattle", province="WA", country="US")
        model_helper.create_provider_city(provider.name, code="30", name="New York City", province="NY", country="US")

        CityMap.objects.create(simplenight_city_id=1, provider=provider, provider_city_id=10)
        CityMap.objects.create(simplenight_city_id=2, provider=provider, provider_city_id=20)

        provider_city_sfo = location_service.find_provider_location(provider.name, 1)
        self.assertEqual("San Francisco", provider_city_sfo.location_name)

        provider_city_sea = location_service.find_provider_location(provider.name, 2)
        self.assertEqual("Seattle", provider_city_sea.location_name)

        self.assertIsNone(location_service.find_provider_location(provider.name, 3))

    def test_find_by_prefix_preferred_first(self):
        cities = location_service.find_by_prefix("Los ")
        self.assertEqual(1, len(cities))
        self.assertEqual("Los Angeles", cities[0].location_name)
