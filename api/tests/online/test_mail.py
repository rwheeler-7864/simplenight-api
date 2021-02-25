from api.common import mail
from api.models.models import Feature
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestMail(SimplenightTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.stub_feature(Feature.MAILGUN_API_KEY, "4fc764e45639a2008a075f69a0706591-2fbe671d-1bc16189")
        self.stub_feature(Feature.TEST_MODE, "false")

    def test_send_mail(self):
        template_name = "order_confirmation"
        subject = "Simplenight Hotel Reservation"
        recipient = "James Morton"
        to_email = "james@simplenight.com"

        params = {
            "booking_id": "123",
            "order_currency_symbol": "$",
            "order_total": "100.00",
            "hotel_name": "Hotel Foo Bar",
            "hotel_sub_total": "80",
            "record_locator": "8848293472",
            "cancellation_policy": "Partial Refund",
            "hotel_address": "123 Main Street",
            "checkin": "4:00pm",
            "checkout": "12:00pm",
            "resort_fee": "0.00",
            "hotel_taxes": "20.00",
            "hotel_room_type": "Jr. Suite",
            "last_four": "1234",
            "order_base_rate": "80",
            "order_taxes": "20"
        }

        mail.send_mail(template_name, subject, recipient, to_email, variables=params)
