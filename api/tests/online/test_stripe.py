import pytest
from django.test import TestCase

from api.hotel.models.booking_model import SubmitErrorType
from api.models.models import TransactionType
from api.payments import stripe_service
from api.view.exceptions import PaymentException
from api.tests import test_objects


class TestStripe(TestCase):
    def test_charge_token(self):
        payment_token = create_test_token("4242424242424242")  # Card succeeds on charge
        response = stripe_service.charge_token(
            payment_token=payment_token, payment_amount=100, currency_code="USD", description="Test charge"
        )

        assert response.charge_id is not None
        assert response.provider_name == "stripe"
        assert response.transaction_amount == 1.00
        assert response.currency == "USD"

    def test_invalid_card(self):
        payment_token = create_test_token("4000000000000002")  # Card fails on charge
        with pytest.raises(PaymentException) as e:
            stripe_service.charge_token(
                payment_token=payment_token, payment_amount=100, currency_code="USD", description="Test charge"
            )

        assert e.value.error_type == SubmitErrorType.PAYMENT_DECLINED
        assert "Your card was declined" in e.value.detail

    def test_charge_card_without_token(self):
        payment = test_objects.payment("4242424242424242")
        response = stripe_service.charge_card(payment, 100, "USD", "Test charge")

        assert response.charge_id is not None
        assert response.provider_name == "stripe"
        assert response.transaction_amount == 1.00
        assert response.currency == "USD"

    # Works unless account is configured to fail transactions with invalid address
    def test_charge_card_invalid_address(self):
        payment = test_objects.payment("4000000000000010")
        response = stripe_service.charge_card(
            payment=payment, payment_amount=100, currency_code="USD", description="TEST"
        )

        assert response.charge_id is not None
        assert response.provider_name == "stripe"
        assert response.transaction_amount == 1.00
        assert response.currency == "USD"

    # Works unless account is configured to fail transactions with invalid zip code
    def test_charge_card_invalid_zip(self):
        payment = test_objects.payment("4000000000000036")
        response = stripe_service.charge_card(
            payment=payment, payment_amount=100, currency_code="USD", description="TEST"
        )

        assert response.charge_id is not None
        assert response.provider_name == "stripe"
        assert response.transaction_amount == 1.00
        assert response.currency == "USD"

    def test_charge_card_invalid_cvv(self):
        payment = test_objects.payment("4000000000000127")
        with pytest.raises(PaymentException) as e:
            stripe_service.charge_card(payment=payment, payment_amount=100, currency_code="USD", description="TEST")

        assert e.value.error_type == SubmitErrorType.PAYMENT_CARD_CVC_INVALID
        assert "security code is incorrect" in e.value.detail

    def test_generic_processing_error(self):
        payment_token = create_test_token("4000000000000119")  # Card fails on charge
        with pytest.raises(PaymentException) as e:
            stripe_service.charge_token(
                payment_token=payment_token, payment_amount=100, currency_code="USD", description="Test charge"
            )

        assert e.value.error_type == SubmitErrorType.PAYMENT_PROCESSOR_ERROR
        assert "Try again in a little bit" in e.value.detail

    def test_insufficient_funds(self):
        payment_token = create_test_token("4000000000009995")  # Card fails on charge
        with pytest.raises(PaymentException) as e:
            stripe_service.charge_token(
                payment_token=payment_token, payment_amount=100, currency_code="USD", description="Test charge"
            )

        assert e.value.error_type == SubmitErrorType.PAYMENT_INSUFFICIENT
        assert "Your card has insufficient funds" in e.value.detail

    def test_refund_token(self):
        payment_token = create_test_token("4242424242424242")  # Card succeeds on charge
        response = stripe_service.charge_token(
            payment_token=payment_token, payment_amount=100, currency_code="USD", description="Test charge"
        )

        assert response.charge_id is not None
        assert response.provider_name == "stripe"
        assert response.transaction_amount == 1.00
        assert response.currency == "USD"
        assert response.transaction_type == TransactionType.CHARGE

        response = stripe_service.refund_token(
            charge_id=response.charge_id, refund_amount=100, reason="requested_by_customer"
        )

        assert response.charge_id is not None
        assert response.transaction_amount == 1.00
        assert response.currency == "USD"
        assert response.transaction_type == TransactionType.REFUND


def create_test_token(card_num):
    payment = test_objects.payment(card_num)
    return stripe_service.tokenize(payment)
