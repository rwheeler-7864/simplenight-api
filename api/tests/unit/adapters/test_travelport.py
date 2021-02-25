import unittest
from datetime import date

import pytest

from api.hotel.adapters.travelport.hotel_details import TravelportHotelDetailsBuilder
from api.hotel.adapters.travelport.travelport import TravelportHotelSearchBuilder, TravelportHotelAdapter
from api.hotel.models.hotel_api_model import HotelLocationSearch
from api.hotel.models.hotel_common_models import RoomOccupancy
from api.tests.utils import load_test_json_resource


@pytest.mark.skip("Travelport Currently Disabled")
class TestTravelport(unittest.TestCase):
    def _test_hotel_search_builder(self):
        search = TravelportHotelSearchBuilder()
        search.num_adults = 1
        search.checkin = "2020-12-01"
        search.checkout = "2020-12-07"
        search.hotel_location = "SFO"

        results = search.request

        self.assertEqual("P3081850", results["TargetBranch"])
        self.assertEqual("Simplenight", results["BillingPointOfSaleInfo"]["OriginApplication"])
        self.assertEqual("1V", results["HotelSearchModifiers"]["PermittedProviders"]["Provider"])
        self.assertEqual(1, results["HotelSearchModifiers"]["NumberOfAdults"])
        self.assertEqual("SFO", results["HotelSearchLocation"]["HotelLocation"])
        self.assertEqual("2020-12-01", results["HotelStay"]["CheckinDate"])
        self.assertEqual("2020-12-07", results["HotelStay"]["CheckoutDate"])

    def _test_hotel_search_builder_from_search_request(self):
        search_request = HotelLocationSearch(
            location_id="SFO",
            start_date=date(2020, 12, 1),
            end_date=date(2020, 12, 7),
            occupancy=RoomOccupancy(adults=1),
        )

        results = TravelportHotelSearchBuilder.build(search_request)

        self.assertEqual("P3081850", results["TargetBranch"])
        self.assertEqual("Simplenight", results["BillingPointOfSaleInfo"]["OriginApplication"])
        self.assertEqual("1V", results["HotelSearchModifiers"]["PermittedProviders"]["Provider"])
        self.assertEqual(1, results["HotelSearchModifiers"]["NumberOfAdults"])
        self.assertEqual("SFO", results["HotelSearchLocation"]["HotelLocation"])
        self.assertEqual("2020-12-01", results["HotelStay"]["CheckinDate"])
        self.assertEqual("2020-12-07", results["HotelStay"]["CheckoutDate"])

    def _test_hotel_details_request_builder(self):
        request_builder = TravelportHotelDetailsBuilder()
        request_builder.chain_code = "HY"
        request_builder.hotel_code = "123"
        request_builder.currency = "USD"
        request_builder.num_rooms = 2
        request_builder.checkin = "2020-01-01"
        request_builder.checkout = "2020-01-07"

        request = request_builder.request
        self.assertEqual("P3081850", request["TargetBranch"])
        self.assertEqual("Simplenight", request["BillingPointOfSaleInfo"]["OriginApplication"])
        self.assertEqual(2, request["HotelDetailsModifiers"]["NumberOfRooms"])
        self.assertEqual("USD", request["HotelDetailsModifiers"]["PreferredCurrency"])
        self.assertEqual("HY", request["HotelProperty"]["HotelChain"])
        self.assertEqual("123", request["HotelProperty"]["HotelCode"])

        self.assertEqual("2020-01-01", request["HotelDetailsModifiers"]["HotelStay"]["CheckinDate"])
        self.assertEqual("2020-01-07", request["HotelDetailsModifiers"]["HotelStay"]["CheckoutDate"])

    def _test_hotel_details_parse_response(self):
        hotel_details_test_resource = load_test_json_resource("travelport/hotel_details_response.json")
        travelport = TravelportHotelAdapter()
        hotel_details = travelport._parse_details(hotel_details_test_resource)

        self.assertIsNotNone(hotel_details)
        self.assertEqual("LQ", hotel_details.chain_code)
        self.assertEqual("LA QUINTA INN STE AIRPORT NORTH", hotel_details.name)
        self.assertEqual("17352", hotel_details.hotel_code)
        self.assertEqual("3PM", hotel_details.checkin_time)
        self.assertEqual("12N", hotel_details.checkout_time)

        self.assertEqual("South San Francisco", hotel_details.address.city)
        self.assertEqual("CA", hotel_details.address.province)
        self.assertEqual("20 Airport Blvd", hotel_details.address.address1.strip())
        self.assertEqual("US", hotel_details.address.country)
        self.assertEqual("94108", hotel_details.address.postal_code)

        self.assertEqual("C1DA01", hotel_details.hotel_rates[0].rate_plan_type)
        self.assertEqual("2 Queen Nsmk With Free Wifi Free Breakfast", hotel_details.hotel_rates[0].description)
        self.assertEqual("Pay Now  Save Non-cancelable", hotel_details.hotel_rates[0].additional_detail[0])

        self.assertEqual(802.75, hotel_details.hotel_rates[0].total_base_rate.amount)
        self.assertEqual("USD", hotel_details.hotel_rates[0].total_base_rate.currency)

        self.assertEqual("2020-07-16", str(hotel_details.hotel_rates[0].daily_rates[0].rate_date))
        self.assertEqual("2020-07-17", str(hotel_details.hotel_rates[0].daily_rates[1].rate_date))
        self.assertEqual("2020-07-18", str(hotel_details.hotel_rates[0].daily_rates[2].rate_date))
        self.assertEqual("2020-07-19", str(hotel_details.hotel_rates[0].daily_rates[3].rate_date))
        self.assertEqual("2020-07-20", str(hotel_details.hotel_rates[0].daily_rates[4].rate_date))
        self.assertEqual("2020-07-21", str(hotel_details.hotel_rates[0].daily_rates[5].rate_date))
        self.assertEqual("2020-07-22", str(hotel_details.hotel_rates[0].daily_rates[6].rate_date))

        self.assertEqual(118.75, hotel_details.hotel_rates[0].daily_rates[0].base_rate.amount)
        self.assertEqual(109.25, hotel_details.hotel_rates[0].daily_rates[1].base_rate.amount)
        self.assertEqual(109.25, hotel_details.hotel_rates[0].daily_rates[2].base_rate.amount)
        self.assertEqual(109.25, hotel_details.hotel_rates[0].daily_rates[3].base_rate.amount)
        self.assertEqual(118.75, hotel_details.hotel_rates[0].daily_rates[4].base_rate.amount)
        self.assertEqual(118.75, hotel_details.hotel_rates[0].daily_rates[5].base_rate.amount)
        self.assertEqual(118.75, hotel_details.hotel_rates[0].daily_rates[6].base_rate.amount)
