from datetime import datetime, timedelta
from decimal import Decimal

from api.common.common_models import SimplenightModel
from api.common.request_context import get_test_mode
from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.models.models import HotelBooking


class UnmatchedPricelineBooking(SimplenightModel):
    refid: str
    reservation_date: datetime
    trip_id: str
    sales_id: str
    hotel_id: str
    hotel_name: str
    total_price: Decimal
    currency: str
    checkin: datetime
    checkout: datetime
    status: str


class PricelineSalesReport:
    def __init__(self):
        self.transport = PricelineTransport(test_mode=get_test_mode())

    def find_unmatched_bookings(self):
        def create_item(data):
            return UnmatchedPricelineBooking(
                refid=data["refid"],
                reservation_date=datetime.fromisoformat(data["reservation_date_time"]),
                trip_id=data["tripid"],
                sales_id=data["sales_id"],
                hotel_id=data["hotelid"],
                hotel_name=data["hotel_name"],
                total_price=Decimal(data["total"]),
                currency=data["booked_currency"],
                checkin=datetime.fromisoformat(data["check_in_date_time"]),
                checkout=datetime.fromisoformat(data["check_out_date_time"]),
                status=data["status"],
            )

        sales_data = self._get_sales_report()

        priceline_sales_by_sale_id = {str(x["tripid"]): x for x in sales_data}
        sn_bookings = HotelBooking.objects.filter(provider__name=PricelineAdapter.get_provider_name())
        sn_priceline_locators = [x.record_locator for x in sn_bookings]
        priceline_bookings = priceline_sales_by_sale_id.items()

        return [create_item(data) for pcln_id, data in priceline_bookings if pcln_id not in sn_priceline_locators]

    def _get_sales_report(self):
        today = datetime.now().date()

        time_start = f"""{today - timedelta(days=7)}_00:00:00"""
        time_end = f"""{today}_23:59:59"""

        response = self.transport.sales_report(time_start=time_start, time_end=time_end)

        return response["getSharedTRK.Sales.Select.Hotel"]["results"]["sales_data"]
