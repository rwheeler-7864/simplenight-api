import stripe
from stripe.error import CardError

from api import logger
from api.common.request_context import get_config_bool, get_config
from api.hotel.models.booking_model import Payment, SubmitErrorType
from api.models.models import PaymentTransaction, TransactionType, Feature
from api.view.exceptions import PaymentException
from common import utils

STRIPE_TEST_API_KEY = "sk_test_dCwkIQsjHBI9XBnQggDP5R2v"

STRIPE_ERROR_CODE_MAPPING = {
    "card_declined": SubmitErrorType.PAYMENT_DECLINED,
    "card_not_supported": SubmitErrorType.PAYMENT_CARD_TYPE_NOT_SUPPORTED,
    "currency_not_supported": SubmitErrorType.PAYMENT_TYPE_NOT_ACCEPTED,
    "do_not_honor": SubmitErrorType.PAYMENT_PROCESSOR_ERROR,
    "expired_card": SubmitErrorType.PAYMENT_CARD_EXPIRATION_INVALID,
    "fraudulent": SubmitErrorType.PAYMENT_DECLINED,
    "generic_decline": SubmitErrorType.PAYMENT_DECLINED,
    "incorrect_number": SubmitErrorType.PAYMENT_CARD_NUMBER_INVALID,
    "incorrect_cvc": SubmitErrorType.PAYMENT_CARD_CVC_INVALID,
    "incorrect_zip": SubmitErrorType.PAYMENT_BILLING_ADDRESS_INVALID,
    "insufficient_funds": SubmitErrorType.PAYMENT_INSUFFICIENT,
    "invalid_account": SubmitErrorType.PAYMENT_INVALID,
    "invalid_amount": SubmitErrorType.PAYMENT_INVALID,
    "invalid_cvc": SubmitErrorType.PAYMENT_CARD_CVC_INVALID,
    "invalid_expiry_year": SubmitErrorType.PAYMENT_CARD_EXPIRATION_INVALID,
    "invalid_number": SubmitErrorType.PAYMENT_CARD_NUMBER_INVALID,
    "pickup_card": SubmitErrorType.PAYMENT_DECLINED,
    "processing_error": SubmitErrorType.PAYMENT_PROCESSOR_ERROR,
    "stolen_card": SubmitErrorType.PAYMENT_DECLINED,
    "withdrawal_count_limit_exceeded": SubmitErrorType.PAYMENT_INSUFFICIENT,
}


def charge_token(payment_token: str, payment_amount: int, currency_code: str, description: str):
    logger.info(f"Charging Stripe: {payment_amount} {currency_code}")
    try:
        response = stripe.Charge.create(
            api_key=_get_stripe_api_credentials(),
            amount=payment_amount,
            currency=currency_code,
            card=payment_token,
            description=description,
        )

        return _payment_transaction(response, TransactionType.CHARGE, token=payment_token)

    except CardError as e:
        error_code = _get_error_mapping(e)
        logger.error("Exception while charging Stripe card", exc_info=e)

        raise PaymentException(error_type=error_code, detail=str(e))


def refund_token(charge_id: str, refund_amount: int, reason: str):
    if not charge_id:
        raise PaymentException(SubmitErrorType.PAYMENT_INVALID, "Charge ID is null")

    logger.info(f"Refunding Stripe: {refund_amount}")
    try:
        api_key = _get_stripe_api_credentials()
        response = stripe.Refund.create(api_key=api_key, charge=charge_id, amount=refund_amount, reason=reason)
        return _payment_transaction(response, TransactionType.REFUND)
    except CardError as e:
        error_code = _get_error_mapping(e)
        logger.exception("Exception while refunding Stripe card")

        raise PaymentException(error_type=error_code, detail=str(e))


def charge_card(payment: Payment, payment_amount: int, currency_code: str, description: str):
    payment_token = tokenize(payment)
    return charge_token(
        payment_token=payment_token, payment_amount=payment_amount, currency_code=currency_code, description=description
    )


def tokenize(payment: Payment) -> str:
    tokenize_request = {
        "number": payment.payment_card_parameters.card_number,
        "exp_month": payment.payment_card_parameters.expiration_month,
        "exp_year": payment.payment_card_parameters.expiration_year,
        "cvc": payment.payment_card_parameters.cvv,
    }

    api_key = _get_stripe_api_credentials()
    response = stripe.Token.create(api_key=api_key, card=tokenize_request)
    return response["id"]


def _is_success(stripe_response):
    return stripe_response["captured"] is True


def _payment_transaction(stripe_response, transaction_type: TransactionType, token=None) -> PaymentTransaction:
    return PaymentTransaction(
        provider_name="stripe",
        currency=str(stripe_response["currency"]).upper(),
        charge_id=str(stripe_response["id"]),
        transaction_amount=utils.to_dollars(stripe_response["amount"]),
        transaction_status=str(stripe_response["object"]),
        transaction_type=transaction_type,
        payment_token=token,
    )


def _get_error_mapping(error: CardError):
    if error.code == "card_declined":
        decline_code = error.json_body["error"]["decline_code"]
        if decline_code in STRIPE_ERROR_CODE_MAPPING:
            return STRIPE_ERROR_CODE_MAPPING[decline_code]
    else:
        decline_code = error.json_body.get("error", {}).get("code")
        if decline_code in STRIPE_ERROR_CODE_MAPPING:
            return STRIPE_ERROR_CODE_MAPPING[decline_code]

    return SubmitErrorType.PAYMENT_PROCESSOR_ERROR


def _get_test_mode():
    return get_config_bool(Feature.TEST_MODE)


def _get_stripe_api_credentials():
    if _get_test_mode():
        return STRIPE_TEST_API_KEY

    return get_config(Feature.STRIPE_API_KEY)
