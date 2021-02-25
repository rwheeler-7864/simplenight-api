import abc
import asyncio
from datetime import datetime, timedelta, date
from decimal import Decimal
from time import sleep
from typing import Union, Optional

from cachetools import cached

from api import logger
from api.activities.activity_internal_models import ActivityDataCachePayload
from api.common import mail, currencies, request_context, cache_storage
from api.common.request_context import get_request_context
from api.hotel import price_verification_service, provider_cache_service
from api.hotel.adapters import adapter_service
from api.hotel.models.adapter_models import AdapterCancelRequest, AdapterHotel
from api.hotel.models.booking_model import (
    HotelBookingRequest,
    HotelBookingResponse,
    Customer,
    Status,
    HotelReservation,
    MultiProductBookingRequest,
    MultiProductBookingResponse,
    ActivityReservation,
    MultiProductHotelBookingRequest,
    AdapterHotelBookingRequest,
    AdapterActivityBookingRequest,
    ActivityBookingItem,
    AdapterActivityBookingItem,
)
from api.hotel.models.hotel_api_model import (
    SimplenightRoomType,
    CancelRequest,
    CancelResponse,
    CancellationDetails,
    CancellationSummary,
    HotelItineraryItem,
    CancelConfirmResponse,
    RoomDataCachePayload,
)
from api.hotel.models.hotel_common_models import Money, RoomRate
from api.models import models
from api.models.models import (
    BookingStatus,
    Traveler,
    Provider,
    HotelBooking,
    Booking,
    HotelCancellationPolicy,
    ProviderHotel,
    PaymentTransaction,
    RecordLocator,
    Feature,
    ActivityBookingModel,
    ActivityBookingItemModel,
)
from api.payments import payment_service
from api.view.exceptions import BookingException, BookingErrorCode
from common.exceptions import AppException


def book_hotel(booking_request: HotelBookingRequest) -> HotelBookingResponse:
    hotel_booking_request = MultiProductHotelBookingRequest(
        hotel_id=booking_request.hotel_id, room_code=booking_request.room_code, traveler=booking_request.traveler
    )

    multi_booking_request = MultiProductBookingRequest(
        api_version=booking_request.api_version,
        transaction_id=booking_request.transaction_id,
        language=booking_request.language,
        customer=booking_request.customer,
        payment=booking_request.payment,
        hotel_booking=hotel_booking_request,
        activity_booking=None,
        additional_info=booking_request.additional_info,
    )

    booking_response = book(multi_booking_request)
    return HotelBookingResponse(
        api_version=booking_response.api_version,
        transaction_id=booking_response.transaction_id,
        status=booking_response.status,
        booking_id=booking_response.booking_id,
        reservation=booking_response.hotel_reservation,
    )


def book(booking_request: MultiProductBookingRequest) -> MultiProductBookingResponse:
    """
    Orchestrates booking multiple products in a single transaction.
    Prevents duplicate bookings, by creating a lock key in Redis.
    Calculates a total price for all products, collects a payment,
    retrieves the Adapter (pre-markup) product cached during availability,
    creates an adapter for each product to book and completes a booking for that product.
    In the event of an error while booking a product, any already-booked products are added to a cancel queue,
    and payment is refunded.
    """

    logger.info(f"Received Booking Request: {booking_request}")
    existing_booking_response = _lock_booking(booking_request)  # See duplicate booking logic comment in function
    if existing_booking_response and isinstance(existing_booking_response, MultiProductBookingResponse):
        logger.warn(f"Found an existing booking existing_booking_response! Txid={booking_request.transaction_id}")
        logger.warn(f"Response: {existing_booking_response}")

        return existing_booking_response

    try:
        logger.info("Persisting traveler and booking")
        traveler = _persist_traveler(booking_request.customer)
        booking = _persist_booking_record(booking_request, traveler)
        simplenight_record_locator = RecordLocator.generate_record_locator(booking)
        logger.info(f"Saved booking {booking.booking_id} {simplenight_record_locator}")

        # Create Product-specific booking processors
        hotel_processor = HotelBookingProcessor(booking_request, booking)
        activity_processor = ActivityBookingProcessor(booking_request, booking)
        all_processors = [hotel_processor, activity_processor]

        total_payment_amount = _calculate_total_amount(hotel_processor, activity_processor)

        logger.info(f"Authorizing payment for {total_payment_amount}")
        auth_response = payment_service.authorize_payment(
            amount=total_payment_amount,
            payment=booking_request.payment,
            description=f"Simplenight Hotel Booking {simplenight_record_locator}",
        )

        if not auth_response:
            logger.error(f"Could not authorize payment for booking: {booking_request}")
            raise AppException("Error authorizing payment")
        elif auth_response.charge_id is not None:
            logger.info(f"Successfully charged Charge ID {auth_response.charge_id}")
            auth_response.booking = booking
            auth_response.save()

        try:
            hotel_reservation = hotel_processor.book()
            activity_reservation = activity_processor.book()

            _set_booked_status(booking)
            if hotel_processor.cached_hotel:
                _send_confirmation_email(
                    hotel=hotel_processor.cached_hotel.adapter_hotel,
                    hotel_reservation=hotel_reservation,
                    activity_reservation=activity_reservation,
                    payment=auth_response,
                    record_locator=simplenight_record_locator,
                )

            booking_response = MultiProductBookingResponse(
                api_version=1,
                transaction_id=booking_request.transaction_id,
                booking_id=simplenight_record_locator,
                status=Status(success=True, message="success"),
                hotel_reservation=hotel_reservation,
                activity_reservation=activity_reservation,
            )

            _unlock_booking(booking_request, booking_response)

            return booking_response

        except Exception as e:
            logger.exception(f"Booking Error.  Refunding {auth_response.charge_id} {auth_response.transaction_amount}")
            refund(booking, auth_response, total_payment_amount.amount)
            for processor in all_processors:
                processor.cancel_reservation()

            logger.error(f"Setting booking {booking.booking_id} to state FAILED")
            booking.booking_status = BookingStatus.FAILED.value
            booking.save()

            _unlock_booking(booking_request, None)
            raise BookingException(BookingErrorCode.PROVIDER_BOOKING_FAILURE, str(e))

    except BookingException as e:
        logger.exception("Error during booking")
        _unlock_booking(booking_request, None)
        raise e
    except Exception as e:
        logger.exception("Unhandled error during booking")
        _unlock_booking(booking_request, None)
        raise BookingException(BookingErrorCode.UNHANDLED_ERROR, str(e))


def _calculate_total_amount(*processors):
    """Calculates a total price for all booking processors, verifying currencies match"""
    booking_currencies = set(x.total_price.currency for x in processors if x.total_price is not None)
    if len(booking_currencies) > 1:
        raise BookingException(BookingErrorCode.MISMATCHED_CURRENCIES, f"Mismatched currencies: {booking_currencies}")

    total_price = sum(x.total_price.amount for x in processors if x.total_price is not None)
    return Money(amount=total_price, currency=next(iter(booking_currencies)))


def _lock_booking(booking_request: MultiProductBookingRequest) -> Optional[MultiProductBookingResponse]:
    """To prevent duplicate bookings, we set a cache key with the customer's first and last name.
    If we detect this key exists, we wait up to 25 seconds for a booking result from another process, and return that.
    Otherwise, we raise a duplicate booking error.
    """

    booking_request_lock_key = _get_booking_request_lock_key(booking_request)
    logger.info(f"Setting Duplicate Booking Lock: {booking_request_lock_key}")
    if not cache_storage.exists(booking_request_lock_key):
        cache_storage.set(booking_request_lock_key, booking_request, timeout=30)
        return None

    booking_response_key = _get_booking_response_lock_key(booking_request)
    deadline = datetime.now() + timedelta(seconds=25)
    while datetime.now() < deadline:
        logger.info(f"Polling for a booking response: {booking_response_key}")
        if cache_storage.exists(booking_response_key):
            response = cache_storage.get(booking_response_key)
            return response
        else:
            sleep(0.5)

    raise BookingException(BookingErrorCode.DUPLICATE_BOOKING, detail="Duplicate booking detected")


def _unlock_booking(book_request: MultiProductBookingRequest, book_response: Optional[MultiProductBookingResponse]):
    booking_request_lock_key = _get_booking_request_lock_key(book_request)
    booking_response_lock_key = _get_booking_response_lock_key(book_request)

    logger.info(f"Setting a booking response: {booking_response_lock_key}")
    cache_storage.set(booking_response_lock_key, book_response, timeout=60)

    logger.info(f"Unsetting booking lock: {booking_request_lock_key}")
    cache_storage.unset(booking_request_lock_key)


def _get_booking_request_lock_key(booking_request: MultiProductBookingRequest):
    customer = booking_request.customer
    return f"booking_lock_request__{customer.first_name}_{customer.last_name}"


def _get_booking_response_lock_key(booking_request: MultiProductBookingRequest):
    customer = booking_request.customer
    return f"booking_lock_response__{customer.first_name}_{customer.last_name}"


def _get_cached_hotel_payload(hotel_booking_request: HotelBookingRequest):
    if not hotel_booking_request:
        return None

    hotel_room_code = hotel_booking_request.room_code
    return provider_cache_service.get_cached_room_data(hotel_room_code)


def _hotel_price_verification(provider: str, rate: Union[SimplenightRoomType, RoomRate]):
    price_verification = price_verification_service.recheck(provider=provider, room_rate=rate)

    if not price_verification.is_allowed_change:
        old_price = rate.total.amount
        new_price = price_verification.verified_room_rate.total.amount
        error_msg = f"Price Verification Failed: Old={old_price}, New={new_price}"
        raise BookingException(BookingErrorCode.PRICE_VERIFICATION, error_msg)

    return price_verification.verified_room_rate


def cancel_lookup(cancel_request: CancelRequest) -> CancelResponse:
    simplenight_locator = cancel_request.booking_id
    last_name = cancel_request.last_name

    logger.info(f"Looking up cancellation policy for recloc={simplenight_locator}")

    try:
        booking = _find_booking_with_booking_id_and_lastname(simplenight_locator, last_name)
        hotel_booking = HotelBooking.objects.get(booking_id=booking.booking_id)
        policy = _find_active_cancellation_policy(booking.booking_id)
        itinerary = _create_itinerary(hotel_booking)
        cancellation_type = _get_cancellation_type(policy)
        description = _get_policy_description(policy)

        original_payment = PaymentTransaction.objects.get(booking_id=booking.booking_id)
        refund_amount = _get_refund_amount(original_payment, policy)
        penalty_amount = _get_penalty_amount(original_payment, policy)

        policy = CancelResponse(
            is_cancellable=_is_cancellable(policy),
            booking_status=BookingStatus.from_value(booking.booking_status),
            itinerary=itinerary,
            details=CancellationDetails(
                cancellation_type=cancellation_type,
                description=description,
                begin_date=policy.begin_date,
                end_date=policy.end_date,
                penalty_amount=penalty_amount,
                penalty_currency=original_payment.currency,
                refund_amount=refund_amount,
                refund_currency=original_payment.currency,
            ),
        )

        logger.info(f"Found cancellation policy: {policy}")
        return policy

    except Booking.DoesNotExist:
        raise BookingException(
            BookingErrorCode.CANCELLATION_FAILURE,
            f"Could not find booking with ID {simplenight_locator} for last name {last_name}",
        )
    except HotelCancellationPolicy.DoesNotExist:
        raise BookingException(BookingErrorCode.CANCELLATION_FAILURE, "Could not find cancellation policies")
    except HotelBooking.DoesNotExist:
        raise BookingException(BookingErrorCode.CANCELLATION_FAILURE, "Could not load hotel booking")


def _get_penalty_amount(payment: PaymentTransaction, policy: HotelCancellationPolicy) -> Decimal:
    if policy.get_cancellation_type() == CancellationSummary.NON_REFUNDABLE:
        penalty_amount = payment.transaction_amount
    elif policy.get_cancellation_type() == CancellationSummary.FREE_CANCELLATION:
        penalty_amount = 0
    else:
        penalty_amount = policy.penalty_amount

    return penalty_amount


def _get_refund_amount(payment: PaymentTransaction, policy: HotelCancellationPolicy) -> Decimal:
    penalty_amount = _get_penalty_amount(payment, policy)

    refund_amount = abs(payment.transaction_amount) - abs(penalty_amount)
    return min(payment.transaction_amount, refund_amount)


def _get_policy_description(policy):
    description = policy.description
    if not description:
        description = "Booking is non-refundable"

    return description


def _is_cancellable(cancellation_policy):
    cancellation_type = _get_cancellation_type(cancellation_policy)
    if cancellation_type in [CancellationSummary.FREE_CANCELLATION, CancellationSummary.PARTIAL_REFUND]:
        return True

    return False


def _get_cancellation_type(policy):
    cancellation_type = CancellationSummary.NON_REFUNDABLE
    if policy.cancellation_type:
        cancellation_type = CancellationSummary.from_value(policy.cancellation_type)
    return cancellation_type


def _find_active_cancellation_policy(booking_id) -> HotelCancellationPolicy:
    current_date = datetime.now().date()
    cancellation_policies = HotelCancellationPolicy.objects.filter(hotel_booking__booking__booking_id=booking_id)
    if len(cancellation_policies) == 1:
        return cancellation_policies[0]

    for policy in cancellation_policies:
        if policy.begin_date < current_date < policy.end_date:
            return policy

    raise BookingException(BookingErrorCode.CANCELLATION_FAILURE, "Could not find eligible cancellation policy")


def _create_itinerary(hotel_booking):
    return HotelItineraryItem(
        name=hotel_booking.hotel_name,
        price=Money(amount=hotel_booking.total_price, currency=hotel_booking.currency),
        confirmation=hotel_booking.record_locator,
        start_date=hotel_booking.checkin,
        end_date=hotel_booking.checkout,
        address=_get_itinerary_address(hotel_booking),
    )


def _get_itinerary_address(hotel_booking):
    hotel = ProviderHotel.objects.filter(
        provider=hotel_booking.provider, provider_code=hotel_booking.provider_hotel_id, language_code="en"
    )

    if len(hotel) > 0:
        return hotel[0].get_address()


def cancel_confirm(cancel_request: CancelRequest) -> CancelConfirmResponse:
    simplenight_locator = cancel_request.booking_id
    last_name = cancel_request.last_name.strip()

    try:
        logger.info(f"Confirming cancellation for recloc={simplenight_locator}")
        booking = _find_booking_with_booking_id_and_lastname(simplenight_locator, last_name)
        booking_status = BookingStatus.from_value(booking.booking_status)
        if booking_status != BookingStatus.BOOKED:
            logger.error("Cannot cancel booking, booking is not in booked state")
            raise BookingException(BookingErrorCode.CANCELLATION_FAILURE, "Booking is not currently active")

        hotel_bookings = list(HotelBooking.objects.filter(booking_id=booking.booking_id))
        traveler = booking.lead_traveler

        cancellation_policy = _find_active_cancellation_policy(booking.booking_id)
        cancellation_type = _get_cancellation_type(cancellation_policy)
        if cancellation_type == CancellationSummary.NON_REFUNDABLE:
            logger.error("Cannot cancel booking, booking is non-refundable")
            raise BookingException(BookingErrorCode.CANCELLATION_FAILURE, "Booking is not cancellable")

        original_payment = PaymentTransaction.objects.get(booking_id=booking.booking_id)
        refund_amount = _get_refund_amount(original_payment, cancellation_policy)
        if refund_amount > 0 and original_payment.currency != cancellation_policy.penalty_currency:
            logger.error("Cancellation policy and booking do not match")
            raise BookingException(
                BookingErrorCode.CANCELLATION_FAILURE, "Cancellation policy currency and booking do not match"
            )

        adapter_cancellation_response = adapter_cancel(hotel_bookings[0], traveler)

        if original_payment.currency != cancellation_policy.penalty_currency:
            raise BookingException(
                BookingErrorCode.CANCELLATION_FAILURE, "Cancellation policy currency and booking do not match"
            )

        refund(booking, original_payment, refund_amount)
        booking.booking_status = BookingStatus.CANCELLED.value
        booking.save()

        logger.info(f"Successfully cancelled recloc {simplenight_locator}, booking ID {booking.booking_id}")
        return CancelConfirmResponse(
            booking_id=str(booking.booking_id),
            record_locator=simplenight_locator,
            booking_status=BookingStatus.CANCELLED,
            cancelled=adapter_cancellation_response.is_cancelled,
            amount_refunded=refund_amount,
        )

    except HotelBooking.DoesNotExist:
        raise BookingException(
            BookingErrorCode.CANCELLATION_FAILURE,
            f"Could not find booking with ID {simplenight_locator} for last name {last_name}",
        )
    except Booking.DoesNotExist:
        raise BookingException(
            BookingErrorCode.CANCELLATION_FAILURE,
            f"Could not find booking with ID {simplenight_locator} for last name {last_name}",
        )
    except HotelCancellationPolicy.DoesNotExist:
        raise BookingException(BookingErrorCode.CANCELLATION_FAILURE, "Could not find cancellation policies")


def refund(booking, original_payment, refund_amount):
    if refund_amount <= 0:
        logger.info(f"Not processing refund for {refund_amount}")
        return None

    refund_transaction = payment_service.refund_payment(charge_id=original_payment.charge_id, amount=refund_amount)
    refund_transaction.booking = booking
    refund_transaction.save()


def _find_booking_with_booking_id_and_lastname(booking_id, last_name):
    return Booking.objects.get(recordlocator__record_locator=booking_id, lead_traveler__last_name__iexact=last_name)


def adapter_cancel(hotel_booking: HotelBooking, traveler: Traveler):
    hotel_booking = hotel_booking
    adapter_cancel_request = AdapterCancelRequest(
        hotel_id=hotel_booking.provider_hotel_id,
        record_locator=hotel_booking.record_locator,
        email_address=traveler.email_address,
    )

    adapter = adapter_service.get_adapter(hotel_booking.provider.name)

    logger.info(f"Cancelling hotel booking {hotel_booking.hotel_booking_id} in adapter {adapter.get_provider_name()}")
    return adapter.cancel(adapter_cancel_request)


def _send_confirmation_email(
    hotel: AdapterHotel,
    hotel_reservation: HotelReservation,
    activity_reservation: ActivityReservation,
    payment: PaymentTransaction,
    record_locator: str,
):
    try:
        template_name = "order_confirmation"
        subject = f"Simplenight Hotel Reservation {record_locator}"
        recipient = f"{hotel_reservation.customer.first_name} {hotel_reservation.customer.last_name}"
        to_email = hotel_reservation.customer.email

        params = _generate_confirmation_email_params(hotel, hotel_reservation, payment, record_locator)

        if not _is_confirmation_email_enabled():
            logger.info(f"Not sending email without email enabled. Parameters: {params}")
            return None

        mail.send_mail(template_name, subject, recipient, to_email, variables=params)

        if activity_reservation:
            logger.warn(f"Activity reservation not implemented in confirmation email: {activity_reservation}")

    except Exception as e:
        logger.warn(f"Could not send confirmation email: {str(e)}")


def _generate_confirmation_email_params(
    hotel: AdapterHotel, reservation: HotelReservation, payment: PaymentTransaction, record_locator: str
):
    friendly_cancellation_map = {
        CancellationSummary.UNKNOWN_CANCELLATION_POLICY: "Call for cancellation details",
        CancellationSummary.FREE_CANCELLATION: "Free Cancellation",
        CancellationSummary.NON_REFUNDABLE: "Non-refundable",
        CancellationSummary.PARTIAL_REFUND: "Partially-refundable",
    }

    provider_hotel = ProviderHotel.objects.get(
        provider__name=hotel.provider, provider_code=hotel.hotel_id, language_code="en"
    )

    order_currency_symbol = currencies.get_symbol(payment.currency)

    def format_money(amount):
        return f"{order_currency_symbol}{amount:.2f}"

    resort_fees = 0
    if reservation.room_rate.postpaid_fees:
        resort_fees = reservation.room_rate.postpaid_fees.total.amount

    room_type_code = reservation.room_rate.room_type_code
    room_type = next(room_type for room_type in hotel.room_types if room_type.code == room_type_code)

    return {
        "booking_id": str(record_locator),
        "order_total": format_money(reservation.room_rate.total.amount),
        "hotel_name": hotel.hotel_details.name,
        "hotel_sub_total": format_money(reservation.room_rate.total.amount),
        "record_locator": reservation.locator.id,
        "cancellation_policy": friendly_cancellation_map.get(reservation.cancellation_details[0].cancellation_type),
        "hotel_address": provider_hotel.address_line_1,
        "checkin": "04:00pm",
        "checkout": "12:00pm",
        "resort_fee": format_money(resort_fees),
        "hotel_taxes": format_money(reservation.room_rate.total_tax_rate.amount),
        "hotel_room_type": room_type.name,
        "last_four": "0000",
        "order_base_rate": format_money(reservation.room_rate.total_base_rate.amount),
        "order_taxes": format_money(reservation.room_rate.total_tax_rate.amount),
    }


def _is_confirmation_email_enabled():
    return request_context.get_config_bool_default(Feature.EMAIL_ENABLED, False)


def _set_booked_status(booking: Booking):
    logger.info(f"Updating booking {booking.booking_id} to BOOKED status")
    booking.booking_status = BookingStatus.BOOKED.value
    booking.save()


def _persist_booking_record(booking_request, traveler):
    booking = models.Booking(
        booking_status=BookingStatus.PENDING.value,
        transaction_id=booking_request.transaction_id,
        organization=get_request_context().get_organization(),
        booking_date=datetime.now(),
        lead_traveler=traveler,
    )

    booking.save()
    return booking


def _persist_traveler(customer: Customer):
    traveler = Traveler(
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone_number=customer.phone_number,
        email_address=customer.email,
        country=customer.country[:2],
    )

    traveler.save()
    return traveler


class BookingProcessor(abc.ABC):
    @property
    @abc.abstractmethod
    def total_price(self) -> Money:
        pass

    @abc.abstractmethod
    def book(self) -> Union[HotelReservation, ActivityReservation]:
        pass

    @abc.abstractmethod
    def cancel_reservation(self) -> bool:
        pass


class ActivityBookingProcessor(BookingProcessor):
    def __init__(self, booking_request: MultiProductBookingRequest, booking: Booking):
        self.booking_request = booking_request
        self.activity_booking_request = self.booking_request.activity_booking
        self.booking = booking
        self.booked_reservation: Optional[ActivityReservation] = None
        self.activity_booking_model: Optional[ActivityBookingModel] = None

    def book(self) -> Optional[ActivityReservation]:
        if self.activity_booking_request is None:
            return None

        logger.info(f"Booking activity: {self.booking_request.activity_booking}")
        adapter_booking_request = self._get_adapter_booking_request()
        adapter = adapter_service.get_activity_adapter(self.cached_activity.provider)
        booking_response = asyncio.run(adapter.book(adapter_booking_request, self.booking_request.customer))

        status = Status(success=booking_response.success, message="")
        activity_reservation = ActivityReservation(
            status=status, record_locator=booking_response.record_locator, items=self.activity_booking_request.items
        )

        self.activity_booking_model = self._persist_activity_reservation()
        self.booked_reservation = activity_reservation

        return activity_reservation

    def cancel_reservation(self) -> bool:
        if not self.booked_reservation:
            logger.info("No activity booking to cancel")
            return True

        try:
            logger.info(f"Cancelling activity booking: {self.booked_reservation}")
            adapter = adapter_service.get_adapter(self.cached_activity.provider)

            adapter.cancel(self.booked_reservation.record_locator.id)
        except Exception as e:
            logger.critical(f"Failure to cancel activity booking: {self.booked_reservation} {e}")

    @property
    def total_price(self) -> Optional[Money]:
        if not self.activity_booking_request:
            return None

        total_amount = sum(x.price * x.quantity for x in self._get_adapter_booking_items())
        return Money(amount=total_amount, currency=self.cached_activity.currency)

    @property
    @cached(cache={})
    def cached_activity(self) -> Optional[ActivityDataCachePayload]:
        if not self.booking_request.activity_booking:
            return None

        return provider_cache_service.get_cached_activity(self.booking_request.activity_booking.code)

    def _get_adapter_booking_items(self):
        """Retrieves stored ActivityVariants, and updates ActivityBookingItem with a price from the cache"""

        def _get_adapter_activity_booking_item(item: ActivityBookingItem):
            @cached(cache={})
            def _retrieve_from_cache(c_activity_code: str, c_activity_date: date, variant_code: str):
                return provider_cache_service.get_activity_variant(c_activity_code, c_activity_date, variant_code)

            activity_code = self.booking_request.activity_booking.code
            activity_date = self.booking_request.activity_booking.activity_date

            cached_activity_variant = _retrieve_from_cache(activity_code, activity_date, item.code)
            return AdapterActivityBookingItem(
                code=item.code, quantity=item.quantity, price=cached_activity_variant.price,
            )

        return list(map(_get_adapter_activity_booking_item, self.booking_request.activity_booking.items))

    def _get_adapter_booking_request(self):
        """Retrieves the stored adapter activity from the cache,
        and converts a booking request into a request suitable for an adapter.
        Among other things, the `code` from the API booking request is substitued
        for a provider code from by an adapter in availability.
        """

        if not self.booking_request.activity_booking:
            return None

        adapter_booking_request = AdapterActivityBookingRequest(
            code=self.cached_activity.code,
            language_code=self.booking_request.activity_booking.language_code,
            activity_date=self.booking_request.activity_booking.activity_date,
            activity_time=self.booking_request.activity_booking.activity_time,
            currency=self.booking_request.activity_booking.currency,
            notes=self.booking_request.activity_booking.notes,
            data=self.booking_request.activity_booking.data,
            misc=self.booking_request.activity_booking.misc,
            supplier_date=self.booking_request.activity_booking.supplier_date,
            items=self._get_adapter_booking_items(),
        )

        return adapter_booking_request

    def _persist_activity_reservation(self):
        provider = Provider.objects.get_or_create(name=self.cached_activity.provider)[0]
        activity_booking = ActivityBookingModel.objects.create(
            provider=provider,
            booking=self.booking,
            activity_name=self.cached_activity.adapter_activity.name,
            activity_code=self.cached_activity.adapter_activity.code,
            activity_date=self.cached_activity.adapter_activity.activity_date,
            activity_time=self.activity_booking_request.activity_time,
            thumbnail=self._get_thumbnail_url(),
            currency=self.cached_activity.simplenight_activity.total_price.currency,
            total_price=self.total_price.amount,
            provider_price=self.total_price.amount,
        )

        for item in self._get_adapter_booking_items():
            ActivityBookingItemModel.objects.create(
                activity_reservation=activity_booking, item_code=item.code, quantity=item.quantity, price=item.price
            )

        return activity_booking

    def _get_thumbnail_url(self):
        images = self.cached_activity.adapter_activity.images
        if images:
            return images[0].url

        return None


class HotelBookingProcessor(BookingProcessor):
    def __init__(self, booking_request: MultiProductBookingRequest, booking: Booking):
        self.booking_request = self._get_hotel_booking_request(booking_request)
        self.booking = booking
        self.booked_reservation: Optional[HotelReservation] = None
        self.hotel_booking: Optional[HotelBooking] = None

    def book(self) -> Optional[HotelReservation]:
        if not self.booking_request:
            return None

        provider = self.cached_hotel.provider
        simplenight_rate = self.cached_hotel.simplenight_rate
        provider_rate = self.cached_hotel.provider_rate

        adapter_booking_request = self.get_adapter_booking_request()

        # Verify rates, and use the rate code from verification.  If prices mismatched above, error will raise
        logger.info("Starting price verification")
        verified_rates = _hotel_price_verification(provider=provider, rate=provider_rate)
        adapter_booking_request.room_code = verified_rates.code

        adapter = self._get_adapter()
        reservation: HotelReservation = adapter.book(adapter_booking_request)
        reservation.room_rate = simplenight_rate  # TODO: Don't create Reservation in Adapter
        reservation.hotel_id = self.booking_request.hotel_id

        if not reservation or not reservation.locator:
            logger.error(f"Could not book hotel: {self.booking_request}")
            raise AppException("Error during hotel booking")

        self.hotel_booking = self._persist_hotel(reservation)
        self.booked_reservation = reservation

        return reservation

    @property
    def total_price(self) -> Optional[Money]:
        if not self.booking_request:
            return None

        return self.cached_hotel.simplenight_rate.total

    @property
    @cached(cache={})
    def cached_hotel(self) -> Optional[RoomDataCachePayload]:
        if not self.booking_request:
            return None

        return provider_cache_service.get_cached_room_data(self.booking_request.room_code)

    def get_adapter_booking_request(self):
        return AdapterHotelBookingRequest(
            transaction_id=self.booking_request.transaction_id,
            hotel_id=self.cached_hotel.adapter_hotel.hotel_id,
            room_code=self.cached_hotel.provider_rate.code,
            language=self.booking_request.language,
            customer=self.booking_request.customer,
            traveler=self.booking_request.traveler,
            additional_info=self.booking_request.additional_info,
        )

    def _persist_hotel(self, reservation):
        # Takes the original room rates as a parameter
        # Persists both the provider rate (on book_request) and the original rates
        simplenight_rate = reservation.room_rate
        provider_rate = self.cached_hotel.provider_rate
        adapter_hotel = self.cached_hotel.adapter_hotel
        provider = Provider.objects.get(name=self.cached_hotel.provider)
        hotel_booking = models.HotelBooking(
            provider=provider,
            booking=self.booking,
            created_date=datetime.now(),
            hotel_name=adapter_hotel.hotel_details.name,
            simplenight_hotel_id=self.booking_request.hotel_id,
            provider_hotel_id=self.cached_hotel.adapter_hotel.hotel_id,
            record_locator=reservation.locator.id,
            total_price=simplenight_rate.total.amount,
            currency=simplenight_rate.total.currency,
            provider_total=provider_rate.total.amount,
            provider_currency=provider_rate.total.currency,
            checkin=adapter_hotel.start_date,
            checkout=adapter_hotel.end_date,
        )

        hotel_booking.save()

        cancellation_details = reservation.cancellation_details
        cancellation_policy_models = []
        for cancellation_policy in cancellation_details:
            cancellation_policy_models.append(
                models.HotelCancellationPolicy(
                    hotel_booking=hotel_booking,
                    cancellation_type=cancellation_policy.cancellation_type.value,
                    description=cancellation_policy.description,
                    begin_date=cancellation_policy.begin_date,
                    end_date=cancellation_policy.end_date,
                    penalty_amount=cancellation_policy.penalty_amount,
                    penalty_currency=cancellation_policy.penalty_currency,
                )
            )

        if len(cancellation_policy_models) > 0:
            logger.info(f"Persisting cancellation policies for hotel booking: {hotel_booking.hotel_booking_id}")
            models.HotelCancellationPolicy.objects.bulk_create(cancellation_policy_models)

        return hotel_booking

    @staticmethod
    def _get_hotel_booking_request(booking_request: MultiProductBookingRequest) -> Optional[HotelBookingRequest]:
        # TODO: Temporary scaffolding for refactor
        if booking_request.hotel_booking:
            return HotelBookingRequest(
                api_version=booking_request.api_version,
                transaction_id=booking_request.transaction_id,
                hotel_id=booking_request.hotel_booking.hotel_id,
                room_code=booking_request.hotel_booking.room_code,
                language=booking_request.language,
                customer=booking_request.customer,
                traveler=booking_request.hotel_booking.traveler,
                payment=booking_request.payment,
                additional_info=booking_request.additional_info,
            )

        return None

    def cancel_reservation(self) -> bool:
        if not self.booked_reservation:
            logger.info("No hotel reservation to cancel")
            return True

        try:
            adapter_cancel_request = AdapterCancelRequest(
                hotel_id=self.hotel_booking.provider_hotel_id,
                record_locator=self.hotel_booking.record_locator,
                email_address=self.booking.lead_traveler.email_address,
            )

            adapter = self._get_adapter()
            logger.info(f"Cancelling hotel booking {self.booked_reservation.hotel_locator}")
            adapter.cancel(adapter_cancel_request)

            return True
        except Exception:
            logger.critical(f"Could not cancel booking: {self.booked_reservation}")
            return False

    def _get_adapter(self):
        return adapter_service.get_adapter(self.cached_hotel.provider)
