from decimal import Decimal

import pytest

from api.hotel.models.booking_model import Payment, PaymentMethod, SubmitErrorType
from api.hotel.models.hotel_common_models import Address, Money
from api.models.models import TransactionType, Feature
from api.payments import payment_service
from api.tests import test_objects
from api.tests.online import test_stripe
from api.tests.unit.simplenight_test_case import SimplenightTestCase
from api.view.exceptions import PaymentException


class TestPaymentService(SimplenightTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.stub_feature(Feature.TEST_MODE, "true")

    def test_authorize_payment_token(self):
        payment_token = test_stripe.create_test_token("4242424242424242")

        amount = Money(amount=Decimal("1.00"), currency="USD")
        payment = Payment(
            payment_card_parameters=None,
            billing_address=Address(
                address1="123 Street Way", city="San Francisco", province="CA", country="US", postal_code="94111"
            ),
            payment_token=payment_token,
            payment_method=PaymentMethod.PAYMENT_TOKEN,
        )

        payment_description = "Test Payment"

        result = payment_service.authorize_payment(amount, payment, payment_description)
        assert result.charge_id is not None

    def test_authorize_payment_card(self):
        payment = test_objects.payment("4000000000000077")
        payment_description = "Test Payment"
        amount = Money(amount=Decimal("1.05"), currency="USD")

        result = payment_service.authorize_payment(amount, payment, payment_description)
        assert result.charge_id is not None
        assert result.payment_token is not None
        assert result.payment_token.startswith("tok_")
        assert result.transaction_amount == Decimal("1.05")

    def test_refund_payment_card(self):
        payment = test_objects.payment("4000000000000077")
        payment_description = "Test Payment"
        amount = Money(amount=Decimal("1.05"), currency="USD")

        charge_result = payment_service.authorize_payment(amount, payment, payment_description)
        assert charge_result.charge_id is not None

        refund_result = payment_service.refund_payment(charge_result.charge_id, amount=amount.amount)
        self.assertEqual(TransactionType.REFUND, refund_result.transaction_type)
        self.assertEqual(Decimal("1.05"), refund_result.transaction_amount)

    def test_invalid_payment(self):
        payment = test_objects.payment("4000000000000002")  # Card fails
        payment_description = "Failing Payment"
        amount = Money(amount=Decimal("1.10"), currency="USD")

        with pytest.raises(PaymentException) as e:
            payment_service.authorize_payment(amount, payment, payment_description)

        assert e.value.error_type == SubmitErrorType.PAYMENT_DECLINED
        assert "Your card was declined" in e.value.detail
