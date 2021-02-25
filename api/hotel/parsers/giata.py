import requests
from django.conf import settings
from lxml import etree
from requests.auth import HTTPBasicAuth

from api import logger
from api.models.models import Provider, ProviderHotel, ProviderMapping, PropertyInfo, ProviderHotelPhones, PhoneType
from common.utils import chunks


class GiataParser:
    _MULTI_CODE_URL = "https://multicodes.giatamedia.com/webservice/rest/1.0/properties/multi"
    _HOTEL_GUIDE_PROPERTIES_URL = "http://ghgml.giatamedia.com/webservice/rest/1.0/texts"
    _USERNAME = "justin|simplenight.com"
    _PASSWORD = "Developers!23"

    def __init__(self):
        self.auth = HTTPBasicAuth(self._USERNAME, self._PASSWORD)
        self.provider, created = Provider.objects.get_or_create(name="giata")
        self.provider_map = self.get_provider_map()

    def get_properties(self, pagination_link=None):
        endpoint = self._get_multi_code_endpoint(pagination_link)
        response = requests.get(endpoint, auth=self.auth)
        if response.ok:
            return response.content

    @staticmethod
    def get_provider_map():
        return {
            "priceline_partner_network": Provider.objects.get_or_create(name="priceline")[0],
            "iceportal": Provider.objects.get_or_create(name="iceportal")[0],
            "hotelbeds": Provider.objects.get_or_create(name="hotelbeds")[0],
        }

    def execute(self):
        existing_giata_hotels = ProviderHotel.objects.filter(provider=self.provider)
        logger.info(f"Removing {len(existing_giata_hotels)} existing Giata hotels")
        existing_giata_hotels.delete()

        existing_giata_mappings = ProviderMapping.objects.all()
        logger.info(f"Removing {len(existing_giata_mappings)} existing Giata mappings")
        existing_giata_mappings.delete()

        properties_xmlstr = self.get_properties()
        pagination_link = self.parse_properties(properties_xmlstr)

        while pagination_link:
            properties_xmlstr = self.get_properties(pagination_link=pagination_link)
            pagination_link = self.parse_properties(properties_xmlstr)

    def execute_hotel_guide(self):
        existing_property_infos = PropertyInfo.objects.filter(provider=self.provider)

        logger.info(f"Removing {existing_property_infos.count()} property info models")
        existing_property_infos.delete()

        for language_code in settings.GEONAMES_SUPPORTED_LANGUAGES:
            self.execute_hotel_guide_for_language(language_code)
            hotels_for_lang = ProviderHotel.objects.filter(language_code=language_code)
            logger.info(f"Loaded {len(hotels_for_lang)} hotels for language {language_code}")

    def execute_hotel_guide_for_language(self, language_code):
        properties, pagination_link = self.get_hotel_guide_properties(language=language_code)
        if not properties:
            logger.error(f"Could not find any property mappings for language code {language_code}")
            return

        for property_id_chunk in chunks(properties, 500):
            property_id_chunk = list(property_id_chunk)
            self.get_and_persist_hotel_guides(language_code, property_id_chunk)

        while pagination_link:
            properties, pagination_link = self.get_hotel_guide_properties(language_code, pagination_link)
            for property_id_chunk in chunks(properties, 500):
                property_id_chunk = list(property_id_chunk)
                self.get_and_persist_hotel_guides(language_code, property_id_chunk)

    def get_hotel_guide_properties(self, language, pagination_link=None):
        endpoint = self._get_hotel_guide_endpoint(language, pagination_link)
        response = requests.get(endpoint, auth=self.auth)
        if response.ok:
            return self.parse_hotel_guide_properties(response.content)

        return None, None

    def parse_hotel_guide_properties(self, properties_xmlstr):
        doc, pagination_link = self._parse_doc_and_return_pagination_link(properties_xmlstr)
        properties = list(map(lambda x: x.get("giataId"), doc.findall(".//item")))
        return properties, pagination_link

    def get_and_persist_hotel_guides(self, language_code, property_codes):
        payload = {"giataIds[]": property_codes}
        endpoint = self._get_hotel_guide_endpoint(language_code)
        response = requests.post(endpoint, data=payload, auth=self.auth)

        if response.ok:
            models = list(self.parse_hotel_guides(language_code, response.content))
            logger.info(f"Persisting {len(models)} property info models")
            PropertyInfo.objects.bulk_create(models)

    def parse_hotel_guides(self, language_code, properties_xmlstr):
        doc, _ = self._parse_doc_and_return_pagination_link(properties_xmlstr)
        for item in doc.findall(".//item"):
            giata_id = item.get("giataId")
            for section in item.findall(".//section"):
                title = self._find_with_default(section, "title")
                description = self._find_with_default(section, "para")
                if not title or not description:
                    continue

                yield PropertyInfo(
                    provider=self.provider,
                    provider_code=giata_id,
                    language_code=language_code,
                    type=title,
                    description=description,
                )

    def parse_properties(self, properties_xmlstr):
        doc, pagination_link = self._parse_doc_and_return_pagination_link(properties_xmlstr)
        if len(pagination_link) > 0:
            pagination_link = pagination_link[0]
            logger.info("Next URL: " + pagination_link)

        provider_hotels = []
        provider_hotel_phones = []
        provider_mappings = []
        for element in doc.findall(".//property"):
            giata_id = element.get("giataId")
            hotel_name = self._find_with_default(element, "name")
            city_name = self._find_with_default(element, "city")
            country = self._find_with_default(element, "addresses/address[1]/country")
            postal_code = self._find_with_default(element, "addresses/address[1]/postalCode")
            address_line_1 = self._find_with_default(element, "addresses/address[1]/addressLine[@addressLineNumber]")
            address_line_2 = self._find_with_default(element, "addresses/address[2]/addressLine[@addressLineNumber]")
            latitude = self._find_with_default(element, "geoCodes/geoCode/latitude")
            longitude = self._find_with_default(element, "geoCodes/geoCode/longitude")
            phones = element.findall(".//phone")

            model = ProviderHotel(
                provider=self.provider,
                provider_code=giata_id,
                hotel_name=hotel_name,
                city_name=city_name,
                country_code=country,
                postal_code=postal_code,
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                latitude=latitude,
                longitude=longitude,
            )

            if phones is not None:
                for phone in phones:
                    phone_number = phone.text
                    phone_type = PhoneType.from_name(phone.get("tech"))
                    if phone_type and phone_number:
                        phone_model = ProviderHotelPhones(
                            provider_hotel=model,
                            provider=self.provider,
                            provider_code=giata_id,
                            type=phone_type,
                            phone_number=phone_number,
                        )
                        provider_hotel_phones.append(phone_model)

            provider_hotels.append(model)

            provider_codes = element.find("propertyCodes")
            if provider_codes is None:
                continue

            for provider_code in provider_codes:
                provider_name = provider_code.get("providerCode")
                property_code = self._find_with_default(provider_code, "code/value")
                if provider_name not in self.provider_map:
                    continue

                mapping = ProviderMapping(
                    provider=self.provider_map[provider_name], giata_code=giata_id, provider_code=property_code
                )

                provider_mappings.append(mapping)

        try:
            ProviderHotel.objects.bulk_create(provider_hotels)
            ProviderHotelPhones.objects.bulk_create(provider_hotel_phones)
            ProviderMapping.objects.bulk_create(provider_mappings)
        except Exception:
            logger.exception("Error persisting models to DB")

        return pagination_link

    @staticmethod
    def _parse_doc_and_return_pagination_link(properties_xmlstr):
        parser = etree.XMLParser(recover=True, encoding="utf-8")
        doc = etree.fromstring(properties_xmlstr, parser)
        namespaces = {"xlink": "http://www.w3.org/1999/xlink"}
        pagination_link = doc.xpath("./more/@xlink:href", namespaces=namespaces)

        return doc, pagination_link

    def _get_multi_code_endpoint(self, pagination_link=None):
        return self._get_endpoint(self._MULTI_CODE_URL, pagination_link)

    def _get_hotel_guide_endpoint(self, language, pagination_link=None):
        endpoint = self._get_endpoint(self._HOTEL_GUIDE_PROPERTIES_URL, pagination_link)
        return f"{endpoint}/{language}"

    @staticmethod
    def _get_endpoint(url, pagination_link):
        if not pagination_link:
            return url

        return pagination_link

    @staticmethod
    def _find_with_default(element, xpath, default=None):
        child = element.find(xpath)
        if child is not None:
            return child.text

        return default
