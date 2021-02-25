from api import logger
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.management.commands.simplenight_base_command import SimplenightBaseCommand

ENDPOINT_MAPPING = {
    PricelineTransport.Endpoint.AMENITIES: {
        "result_key": "getSharedBOF2.Downloads.Hotel.Amenities",
        "result_sub_key": "amenities",
    },
    PricelineTransport.Endpoint.HOTELS_DOWNLOAD: {
        "result_key": "getSharedBOF2.Downloads.Hotel.Hotels",
        "result_sub_key": "hotels",
    },
    PricelineTransport.Endpoint.PHOTOS_DOWNLOAD: {
        "result_key": "getSharedBOF2.Downloads.Hotel.Photos",
        "result_sub_key": "photos",
    },
    PricelineTransport.Endpoint.HOTEL_CHAINS: {
        "result_key": "getSharedBOF2.Downloads.Hotel.Chains",
        "result_sub_key": "chains",
    },
    PricelineTransport.Endpoint.REVIEWS: {
        "result_key": "getSharedBOF2.Downloads.Hotel.Reviews",
        "result_sub_key": "reviews",
    },
}


def load_data(transport: PricelineTransport, endpoint: PricelineTransport.Endpoint, chunk_size=10000):
    num_loaded = 0
    resume_key = None
    result_key = ENDPOINT_MAPPING[endpoint]["result_key"]
    result_sub_key = ENDPOINT_MAPPING[endpoint]["result_sub_key"]

    while True:
        SimplenightBaseCommand.mock_organization()
        logger.info(f"Making hotels download request to Priceline with resume key {resume_key}")
        response = transport.get(endpoint=endpoint, resume_key=resume_key, limit=chunk_size)
        resume_key = response[result_key]["results"]["resume_key"]
        total_records = response[result_key]["results"]["total_records"]
        result_batch = response[result_key]["results"][result_sub_key]
        num_loaded += len(result_batch)

        logger.info(f"Retrieved {num_loaded}, {total_records-num_loaded} remaining")

        yield result_batch

        if not resume_key or num_loaded == total_records:
            logger.info("Loading complete.")
            return
