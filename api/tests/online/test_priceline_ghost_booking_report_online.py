from api.hotel.adapters.priceline.priceline_sales_report import PricelineSalesReport
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestPricelineGhostBookingReport(SimplenightTestCase):
    def test_sales_report(self):
        report = PricelineSalesReport()
        print(report.find_unmatched_bookings())