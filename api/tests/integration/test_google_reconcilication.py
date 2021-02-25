import csv
import glob
from collections import defaultdict
from datetime import date

from api.management import google_reconciliation
from api.models.models import Organization, ProviderMapping
from api.tests import model_helper
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestGoogleReconciliation(SimplenightTestCase):
    def test_report(self):
        provider = model_helper.create_provider("foo")
        giata_provider = model_helper.create_provider("giata")

        booking_1 = model_helper.create_booking(booking_date=date(2020, 1, 7), organization=self.organization)
        model_helper.create_hotel_booking(booking_1, "Hotel One", "FOO1", "SN1", provider, "123")

        booking_2 = model_helper.create_booking(booking_date=date(2020, 2, 15), organization=self.organization)
        model_helper.create_hotel_booking(booking_2, "Hotel Two", "FOO2", "SN2", provider, "234")

        booking_3 = model_helper.create_booking(booking_date=date(2020, 1, 25), organization=self.organization)
        model_helper.create_hotel_booking(booking_3, "Hotel Three", "FOO3", "SN3", provider, "345")

        diff_organization = Organization.objects.get_or_create(
            name="SOME_OTHER_ORG", api_daily_limit=1, api_burst_limit=1
        )

        booking_4 = model_helper.create_booking(booking_date=date(2020, 1, 25), organization=diff_organization[0])
        model_helper.create_hotel_booking(booking_4, "Hotel Four", "FOO4", "SN4", provider, "456")

        model_helper.create_provider_hotel(giata_provider, "SN1", "Hotel One")
        model_helper.create_provider_hotel(giata_provider, "SN2", "Hotel Two")
        model_helper.create_provider_hotel(giata_provider, "SN3", "Hotel Three")
        model_helper.create_provider_hotel(giata_provider, "SN4", "Hotel Four")

        ProviderMapping.objects.create(provider=provider, giata_code="SN1", provider_code="FOO1")
        ProviderMapping.objects.create(provider=provider, giata_code="SN2", provider_code="FOO2")
        ProviderMapping.objects.create(provider=provider, giata_code="SN3", provider_code="FOO3")
        ProviderMapping.objects.create(provider=provider, giata_code="SN4", provider_code="FOO4")

        report = google_reconciliation.get_report(
            start_date=date(2020, 1, 1), end_date=date(2020, 2, 1), organization=self.organization.name
        )

        self.assertEqual(2, len(report))
        self.assertEqual("SN1", report[0]["hotel_id"])
        self.assertEqual("Hotel One", report[0]["hotel_name"])
        self.assertEqual("123 Simple Way", report[0]["hotel_address"])
        self.assertEqual("Simpleville", report[0]["hotel_city"])

        self.assertEqual("SN3", report[1]["hotel_id"])
        self.assertEqual("Hotel Three", report[1]["hotel_name"])

        csv_report = google_reconciliation.format_report_csv(report)
        reader = csv.reader(csv_report.splitlines())
        rows = list(reader)

        self.assertEqual("SN1", rows[1][0])
        self.assertEqual("Hotel One", rows[1][1])
        self.assertEqual("SN3", rows[2][0])
        self.assertEqual("Hotel Three", rows[2][1])

    def x_test_merge_old_bookings_report(self):
        """This is just a temporary test for merging old Travelport bookings for econcilliation purposes"""

        from lxml import etree

        hotels = defaultdict(dict)
        for file in glob.glob("/Users/jmorton/Downloads/props/Oct052020.xml"):
            doc = etree.parse(file)
            for listing in doc.findall("//listing"):
                hotel_name = listing.find("name").text.upper().strip()
                hotel_id = listing.find("id").text.strip()
                address_line_1 = listing.find("./address/component[@name='addr1']").text.strip()
                country = listing.find("./address/component[@name='country']").text.strip()

                hotels[hotel_name] = {
                    "id": hotel_id,
                    "hotel_name": hotel_name,
                    "address_line_1": address_line_1,
                    "country": country,
                }

                postal_code = listing.findall("./address/component[@name='postal_code']")
                if postal_code and postal_code[0].text:
                    hotels[hotel_name]["postal_code"] = postal_code[0].text.strip()

                phone = listing.findall("phone[@type='main']")
                if phone:
                    hotels[hotel_name]["phone"] = phone[0].text.strip()

        fields = ("id", "hotel_name", "address_line_1", "country", "postal_code", "phone")
        with open("/Users/jmorton/hotels.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writerows(hotels.values())
