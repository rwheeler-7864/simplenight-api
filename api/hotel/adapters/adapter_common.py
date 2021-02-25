from typing import Dict

from cachetools.func import ttl_cache

from api.common.encryption_service import EncryptionService
from api.hotel.models.adapter_models import AdapterLocationSearch
from api.hotel.models.booking_model import PaymentCardParameters, CardType, Payment, PaymentMethod
from api.hotel.models.hotel_common_models import Address
from api.locations import location_service
from api.models.models import ProviderChain, Provider
from api.view.exceptions import AvailabilityException, AvailabilityErrorCode


def get_virtual_credit_card(test_mode=True) -> Payment:
    if test_mode:
        return Payment(
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_card_parameters=PaymentCardParameters(
                card_type=CardType.VI,
                card_number="4242424242424242",
                cardholder_name="Simplenight Test",
                expiration_month="01",
                expiration_year="2025",
                cvv="123",
            ),
            billing_address=Address(
                city="Miami",
                province="FL",
                country="US",
                address1="123 Simplenight Way",
                postal_code="94111",
            ),
        )
    else:
        crypted_card_number = "gA/2oQ2bgDW/JGPpOjpxHrtDskdnpq9atFjqg5YUOwY="
        crypted_card_cvv = "L1BaCNArVeP3WvSIzU9vUw=="
        encryption_service = EncryptionService()

        return Payment(
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_card_parameters=PaymentCardParameters(
                card_type=CardType.VI,
                card_number=encryption_service.decrypt(crypted_card_number),
                cvv=encryption_service.decrypt(crypted_card_cvv),
                cardholder_name="Mark Halberstein",
                expiration_month="03",
                expiration_year="2023",
            ),
            billing_address=Address(
                city="New York",
                province="NY",
                country="US",
                address1="245 East 58th St",
                postal_code="33179",
            ),
        )


@ttl_cache(maxsize=10, ttl=86400)
def get_chain_mapping(provider_name) -> Dict[str, str]:
    chain_mappings = ProviderChain.objects.filter(provider__name=provider_name)
    return {chain_mappings.provider_code: chain_mappings.chain_name}


@ttl_cache(maxsize=10, ttl=86400)
def get_provider(provider_name) -> Provider:
    return Provider.objects.get_or_create(name=provider_name)[0]


def get_provider_location(provider_name, location_id):
    provider_location = location_service.find_provider_location(provider_name, location_id)

    if provider_location is None:
        raise AvailabilityException(
            detail="Could not find provider location mapping", error_type=AvailabilityErrorCode.LOCATION_NOT_FOUND
        )

    return provider_location
