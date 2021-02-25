from django.test import TestCase

from api.locations import airports
from api.models.models import Airport
from api.tests import model_helper


class TestAirports(TestCase):
    def setUp(self) -> None:
        airports.load_openflights_airports_data()

    def test_load_countries(self):
        countries = airports.parse_openflights_countries_data()
        country_code = countries["United States"]

        self.assertEqual("US", country_code)

    def test_load_airports(self):
        sfo_airport = Airport.objects.get(airport_code="SFO")

        self.assertEqual(3469, sfo_airport.airport_id)
        self.assertEqual("San Francisco International Airport", sfo_airport.airport_name)
        self.assertEqual("San Francisco", sfo_airport.city_name)
        self.assertEqual("US", sfo_airport.iso_country_code)
        self.assertAlmostEqual(37.618, sfo_airport.latitude, places=2)
        self.assertAlmostEqual(-122.375, sfo_airport.longitude, places=2)
        self.assertEqual("America/Los_Angeles", sfo_airport.timezone)

    def test_map_airport_exact_city_match(self):
        model_helper.create_geoname(1, "San Francisco", "CA", "US")
        model_helper.create_geoname(2, "Seattle", "WA", "US")
        model_helper.create_geoname(3, "New York", "NY", "US")

        airport_mapping = airports.AirportMapping()

        sfo_airport = Airport.objects.get(airport_code="SFO")
        sea_airport = Airport.objects.get(airport_code="SEA")
        jfk_airport = Airport.objects.get(airport_code="JFK")

        mapped_city = airport_mapping.map_airport(sfo_airport)
        self.assertIsNotNone(mapped_city)
        self.assertEqual("San Francisco", mapped_city.location_name)

        mapped_city = airport_mapping.map_airport(sea_airport)
        self.assertIsNotNone(mapped_city)
        self.assertEqual("Seattle", mapped_city.location_name)

        mapped_city = airport_mapping.map_airport(jfk_airport)
        self.assertIsNotNone(mapped_city)
        self.assertEqual("New York", mapped_city.location_name)

        # No mapping when multiple cities have same name in the country
        model_helper.create_geoname(4, "San Francisco", "XX", "US")
        airport_mapping = airports.AirportMapping()
        mapped_city = airport_mapping.map_airport(sfo_airport)
        self.assertIsNone(mapped_city)

    def test_map_latitude_and_longitude(self):
        model_helper.create_geoname(1, "Foo", "CA", "US", latitude=50.0, longitude=50.0)
        model_helper.create_geoname(2, "Bar", "WA", "US", latitude=49.0, longitude=49.0)
        model_helper.create_geoname(3, "Baz", "NY", "US", latitude=48.0, longitude=48.0)

        airport_mapping = airports.AirportMapping()

        sfo_airport = Airport(city_name="San Francisco", latitude=49.25, longitude=49.25, iso_country_code="US")
        mapped_city = airport_mapping.map_airport(sfo_airport)

        self.assertEqual("Bar", mapped_city.location_name)
