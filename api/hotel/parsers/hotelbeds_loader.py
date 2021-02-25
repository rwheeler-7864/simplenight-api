from api import logger
from api.hotel.adapters.hotelbeds.hotelbeds_transport import HotelbedsTransport
from api.hotel.adapters.hotelbeds.hotelbeds_common_models import HOTELBEDS_LANGUAGE_MAP
from api.management.commands.simplenight_base_command import SimplenightBaseCommand

ENDPOINT_MAPPING = {
    HotelbedsTransport.Endpoint.HOTEL_CONTENT: {
        "result_key": "hotels",
    },
    HotelbedsTransport.Endpoint.CHAINS_TYPES: {
        "result_key": "chains"
    }
}


def load_data(transport: HotelbedsTransport, endpoint: HotelbedsTransport.Endpoint, chunk_size=1000, **params):
    result_key = ENDPOINT_MAPPING[endpoint]["result_key"]
    num_loaded = 0
    from_value = 1
    to_value = chunk_size

    while True:
        SimplenightBaseCommand.mock_organization()
        logger.info(f"Making hotels download request to Hotelbeds from {from_value} to {to_value}")

        params["from"] = from_value
        params["to"] = to_value
        params["fields"] = "all"

        response = transport.get(endpoint=endpoint, **params)
        if not response or "error" in response:
            break
        from_value = response["to"] + 1
        to_value = response["to"] + chunk_size
        total_records = response["total"]
        result_batch = response[result_key]
        num_loaded += len(result_batch)

        logger.info(f"Retrieved {num_loaded}, {total_records - num_loaded} remaining")

        yield result_batch

        if num_loaded >= total_records or total_records == 0:
            break

    logger.info("Loading complete.")
