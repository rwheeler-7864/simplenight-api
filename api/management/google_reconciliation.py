import csv
from datetime import date
from decimal import Decimal
from io import StringIO
from typing import List, Dict, Any

from api.hotel import hotel_mappings
from api.models.models import RecordLocator, ProviderHotel

REPORT_FIELDS = [
    "hotel_id",
    "hotel_name",
    "hotel_address",
    "hotel_city",
    "hotel_postal_code",
    "hotel_country",
    "hotel_phone",
    "booking_id",
    "booking_date",
    "checkin_date",
    "checkout_date",
    "num_rooms",
    "num_travelers",
    "revenue",
    "currency",
    "billing_currency_conversion_rate",
    "booking_status",
    "commission",
    "commission_currency",
    "commission_currency_conversion_rate",
    "payment_date",
    "payment_status",
]


def get_report(organization: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
    commission_rate = Decimal("0.1")

    locators: List[RecordLocator] = (
        RecordLocator.objects.prefetch_related("booking")
        .prefetch_related("booking__lead_traveler")
        .prefetch_related("booking__hotelbooking_set")
        .filter(
            booking__booking_date__gt=start_date,
            booking__booking_date__lte=end_date,
            booking__organization__name=organization,
        )
    )

    rows = []
    for locator in locators:
        for hotel_booking in locator.booking.hotelbooking_set.all():
            provider = hotel_booking.provider
            provider_code = hotel_booking.provider_hotel_id
            simplenight_hotel_id = hotel_mappings.find_simplenight_hotel_id(provider_code, provider.name)
            hotel = ProviderHotel.objects.prefetch_related("phone").get(
                provider__name="giata", provider_code=simplenight_hotel_id
            )

            hotel_phone = hotel.phone.first()
            phone_number = None
            if hotel_phone:
                phone_number = hotel_phone.phone_number

            row = {
                "hotel_id": hotel_booking.simplenight_hotel_id,
                "hotel_name": hotel_booking.hotel_name,
                "hotel_address": hotel.address_line_1,
                "hotel_city": hotel.city_name,
                "hotel_postal_code": hotel.postal_code,
                "hotel_country": hotel.country_code,
                "hotel_phone": phone_number,
                "booking_id": str(locator.booking.booking_id),
                "booking_date": locator.booking.booking_date,
                "checkin_date": hotel_booking.checkin,
                "checkout_date": hotel_booking.checkout,
                "num_rooms": 1,
                "num_travelers": 1,
                "revenue": hotel_booking.total_price,
                "currency": hotel_booking.currency,
                "billing_currency_conversion_rate": 1,
                "booking_status": locator.booking.booking_status,
                "commission": hotel_booking.total_price * commission_rate,
                "commission_currency": hotel_booking.currency,
                "commission_currency_conversion_rate": 1,
                "payment_date": locator.booking.booking_date,
                "payment_status": "Invoice Required",
            }

            rows.append(row)

    return rows


def format_report_csv(report: List[Dict[str, Any]]):
    output = StringIO()
    writer = csv.DictWriter(output, REPORT_FIELDS)
    writer.writeheader()
    writer.writerows(report)

    return output.getvalue()
