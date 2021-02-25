from api import logger
from api.hotel.adapters.hotelbeds.hotelbeds_adapter import HotelbedsAdapter
from api.hotel.adapters.hotelbeds.hotelbeds_transport import HotelbedsTransport
from api.hotel.parsers import hotelbeds_loader
from api.models.models import ProviderChain, Provider


class HotelbedsChainsParser:
    def __init__(self, transport):
        self.transport = transport
        self.hotelbeds = HotelbedsAdapter(transport=transport)
        self.provider = self.hotelbeds.adapter_info.get_or_create_provider_id()

    def load(self, chunk_size=1000, limit=None):
        num_loaded = 0
        chunked_chain_data = hotelbeds_loader.load_data(
            self.transport, HotelbedsTransport.Endpoint.CHAINS_TYPES, chunk_size=chunk_size, useSecondaryLanguage=True)
        for chunk in chunked_chain_data:
            chains = list(map(self.parse_chain, chunk))
            ProviderChain.objects.bulk_create(chains)

            num_loaded += len(chains)
            logger.info(f"Loaded {num_loaded} chains")

            if limit and num_loaded >= limit:
                logger.info(f"Limit reached ({num_loaded} of {limit}). Exiting.")
                return

    def parse_chain(self, chain_data):
        description = ""
        if "description" in chain_data:
            description = chain_data["description"]["content"]

        return ProviderChain(
            provider=self.provider,
            provider_code=chain_data["code"],
            chain_name=description
        )

    @classmethod
    def remove_old_data(cls):
        existing_chains = ProviderChain.objects.filter(provider__name=HotelbedsAdapter.get_provider_name())
        logger.info(f"Removing {existing_chains.count()} existing chains")
        existing_chains.delete()
