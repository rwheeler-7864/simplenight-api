from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.parsers import priceline_loader


class PricelineAmenitiesParser:
    def __init__(self, transport):
        self.transport = transport

    def execute(self):
        priceline_amenities = priceline_loader.load_data(self.transport, PricelineTransport.Endpoint.AMENITIES)
        for results in priceline_amenities:
            for result in results:
                print(result)