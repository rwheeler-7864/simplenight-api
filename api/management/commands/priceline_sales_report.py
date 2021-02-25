from typing import Dict

from api.hotel.adapters.priceline.priceline_sales_report import PricelineSalesReport
from api.management.commands.simplenight_base_command import SimplenightBaseCommand


class UnmatchedSaleItem:
    def __init__(self, sale_item: Dict):
        self.sale_item = sale_item

    def __repr__(self):
        record_locator = self.sale_item["sales_id"]
        hotel_name = self.sale_item["hotel_name"]
        booking_date = self.sale_item["reservation_date_time"]

        return f"""
            Record Locator: {record_locator}
            Hotel Name: {hotel_name}
            Booking Date: {booking_date}"""


class Command(SimplenightBaseCommand):
    def handle(self, *args, **options):
        priceline_sales_report = PricelineSalesReport()
        sales_data = priceline_sales_report.find_unmatched_bookings()

        print(sales_data)