from collections import defaultdict
from typing import DefaultDict, List

from haversine import haversine

from api import logger
from api.models.models import ProviderCity, Geoname, CityMap, Provider


class CityMappingService:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.provider = Provider.objects.get(name=self.provider_name)
        self.simplenight_cities = self.find_unmapped_simplenight_cities()
        self.unmapped_provider_cities = self.find_unmapped_provider_cities()
        self.simplenight_city_name_map: DefaultDict[str, List[Geoname]] = defaultdict(list)
        self.provider_city_name_map: DefaultDict[str, List[ProviderCity]] = defaultdict(list)
        self.provider_by_country: DefaultDict[str, List[ProviderCity]] = defaultdict(list)

        # Create map by location name for quick lookup
        for city in self.unmapped_provider_cities:
            self.provider_city_name_map[city.location_name].append(city)
            self.provider_by_country[city.country_code].append(city)

        for city in self.simplenight_cities:
            self.simplenight_city_name_map[city.location_name].append(city)

        num_unmapped_simplenight = len(self.simplenight_cities)
        num_unmapped_provider = len(self.unmapped_provider_cities)
        logger.info(f"Initializing {self.__class__.__name__}")
        logger.info(f"Found {num_unmapped_simplenight} simplenight cities")
        logger.info(f"Found {num_unmapped_provider} provider cities")

    def find_unmapped_simplenight_cities(self):
        existing_mappings = CityMap.objects.filter(provider__name=self.provider_name).values_list(
            "simplenight_city", flat=True
        )

        return list(Geoname.objects.exclude(geoname_id__in=existing_mappings))

    def find_unmapped_provider_cities(self):
        existing_mappings = CityMap.objects.filter(provider__name=self.provider_name).values_list(
            "provider_city", flat=True
        )

        provider_mappings = ProviderCity.objects.filter(provider__name=self.provider_name)
        return list(provider_mappings.exclude(provider_code__in=existing_mappings))

    def map_cities(self):
        for simplenight_city in self.simplenight_cities:
            exact_matching_provider_city = self._exact_match(simplenight_city)
            if exact_matching_provider_city:
                logger.info(f"Exact Match: {simplenight_city} {exact_matching_provider_city}")
                self._create_match(simplenight_city, exact_matching_provider_city)
                continue

            closest_distance_match = self._nearby_matches(simplenight_city)
            if closest_distance_match:
                logger.info(f"Nearby Match: {simplenight_city.location_name} = {closest_distance_match.location_name}")
                self._create_match(simplenight_city, closest_distance_match)
                continue

    def _exact_match(self, simplenight_city):
        provider_name_matches = self.provider_city_name_map[simplenight_city.location_name]

        for provider_city in provider_name_matches:
            country_matches = provider_city.country_code == simplenight_city.iso_country_code
            province_matches = provider_city.province == simplenight_city.province
            if country_matches and province_matches:
                return provider_city

            if not provider_city.province:
                simplenight_city_matches = self.simplenight_city_name_map[simplenight_city.location_name]
                simplenight_country = simplenight_city.iso_country_code
                provider_name_by_country = [x for x in provider_name_matches if x.country_code == simplenight_country]
                sn_city_match_by_country = [
                    x for x in simplenight_city_matches if x.iso_country_code == simplenight_country
                ]

                if country_matches:
                    if len(provider_name_by_country) == 1 and len(sn_city_match_by_country) == 1:
                        return provider_city

        return None

    def _create_match(self, simplenight_city, provider_city):
        city_map = CityMap.objects.create(
            provider=self.provider,
            simplenight_city_id=simplenight_city.geoname_id,
            provider_city_id=provider_city.provider_code,
        )
        city_map.save()

        logger.info(f"Creating city mapping: {simplenight_city} => {provider_city} - {city_map}")

    def _nearby_matches(self, simplenight_city):
        closest_distance = 10  # Upper distance limit
        closest_match = None

        provider_cities_in_country = self.provider_by_country[simplenight_city.iso_country_code]

        for provider_city in provider_cities_in_country:
            if not simplenight_city.latitude or not provider_city.longitude:
                continue

            # Performance Hack - Don't do any further calc if latitude difference greater than 1 degree
            degrees_difference = abs(simplenight_city.latitude) - abs(simplenight_city.longitude)
            if degrees_difference > 1:
                continue

            simplenight_lat_lon = (simplenight_city.latitude, simplenight_city.longitude)
            provider_lat_lon = (provider_city.latitude, provider_city.longitude)
            distance_in_km = haversine(simplenight_lat_lon, provider_lat_lon)
            if distance_in_km < closest_distance:
                closest_distance = distance_in_km
                closest_match = provider_city

        return closest_match

    def reload(self):
        self.__init__(self.provider_name)
