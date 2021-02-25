from datetime import date

from django.test import TestCase

from api.hotel.models.hotel_common_models import BookingStatus
from api.models.models import RecordLocator, Booking
from api.tests import model_helper


class TestModels(TestCase):
    def test_generate_record_locator(self):
        booking = Booking.objects.create(
            booking_status=BookingStatus.BOOKED.value,
            transaction_id="foo",
            booking_date=date(2020, 1, 1),
            lead_traveler=model_helper.create_traveler()
        )

        locator = RecordLocator.generate_record_locator(booking)
        self.assertEqual(8, len(locator))
