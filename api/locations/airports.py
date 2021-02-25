import csv
from collections import defaultdict
from typing import Dict

import requests
from haversine import haversine

from api import logger
from api.models.models import Airport, Geoname

OPENFLIGHTS_AIRPORT_DATA = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
OPENFLIGHTS_COUNTRY_DATA = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/countries.dat"


class AirportMapping:
    def __init__(self):
        self.cities = list(Geoname.objects.order_by("-population").all())
        self.cities_by_country = defaultdict(list)
        self.cities_by_city_name = defaultdict(list)

        for city in self.cities:
            self.cities_by_country[city.iso_country_code].append(city)
            self.cities_by_city_name[city.location_name].append(city)

    def map_airport(self, airport: Airport):
        matching_cities = self.cities_by_city_name[airport.city_name]
        for city in matching_cities:
            country_matches = city.iso_country_code == airport.iso_country_code
            is_only_city_name_match = len(matching_cities) == 1

            if country_matches and is_only_city_name_match:
                return city

        for city in self.cities_by_country[airport.iso_country_code]:
            airport_geolocation = (airport.latitude, airport.longitude)
            city_geolocation = (city.latitude, city.longitude)
            distance = haversine(airport_geolocation, city_geolocation)

            # In population-sorted list, return first city within 25km
            if distance < 50:
                logger.info(f"Mapping city {city} to {airport}")
                return city


def parse_openflights_countries_data() -> Dict[str, str]:
    csv_reader = _download(OPENFLIGHTS_COUNTRY_DATA)
    return {row[0]: row[1] for row in csv_reader}


def load_openflights_airports_data():
    countries = parse_openflights_countries_data()
    mappings = AirportMapping()
    csv_reader = _download(OPENFLIGHTS_AIRPORT_DATA)

    Airport.objects.all().delete()

    airports = []
    for row in csv_reader:
        airport_id, name, city, country_name, iata, _, latitude, longitude, _, _, _, timezone, *_ = row

        if country_name not in countries:
            logger.info(f"Could not find mapped country code for {country_name}")
            continue

        iso_country_code = countries[country_name]
        airport = Airport(
            airport_id=airport_id,
            airport_name=name,
            city_name=city,
            iso_country_code=iso_country_code,
            airport_code=iata,
            latitude=float(latitude),
            longitude=float(longitude),
            timezone=timezone,
        )

        mapped_city = mappings.map_airport(airport)
        if mapped_city:
            airport.geoname = mapped_city

        airports.append(airport)

    Airport.objects.bulk_create(airports)


def find_by_prefix(name_prefix: str, limit=3):
    return list(Airport.objects.filter(airport_name__istartswith=name_prefix)[:limit])


def find_by_airport_code(airport_code: str):
    try:
        return Airport.objects.get(airport_code=airport_code.upper())
    except Airport.DoesNotExist:
        return None


def _download(url):
    response = requests.get(url)
    if not response.ok:
        logger.info("Receiving invalid response retrieving airports data: {}", response.text)
        return None

    return csv.reader(response.text.splitlines())


if __name__ == "__main__":
    parse_openflights_countries_data()
