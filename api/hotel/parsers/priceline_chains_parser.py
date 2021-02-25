from api import logger
from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.parsers import priceline_loader
from api.models.models import ProviderChain, Provider


class PricelineHotelChainsParser:
    def __init__(self, transport):
        self.transport = transport
        self.provider = Provider.objects.get_or_create(name=PricelineAdapter.get_provider_name())[0]

    def execute(self, limit=None, chunk_size=5000):
        total_loaded = 0
        parser_type = PricelineTransport.Endpoint.HOTEL_CHAINS
        priceline_hotel_chains = priceline_loader.load_data(self.transport, parser_type, chunk_size=chunk_size)
        for results in priceline_hotel_chains:
            models = list(map(self.parse_model, results))
            ProviderChain.objects.bulk_create(models)

            total_loaded += len(models)
            if limit and total_loaded >= limit:
                logger.info(f"Limit of {limit} reached.  Exiting.")
                return

    def parse_model(self, result):
        provider_code = result["chain_id_ppn"]
        chain_name = result["chain_name"]

        return ProviderChain(provider=self.provider, provider_code=provider_code, chain_name=chain_name)

    def remove_old_data(self):
        ProviderChain.objects.filter(provider=self.provider).delete()
