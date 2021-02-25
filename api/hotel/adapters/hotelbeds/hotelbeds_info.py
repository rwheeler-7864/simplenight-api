from api.hotel.adapters.adapter_info import AdapterInfo


class HotelbedsInfo(AdapterInfo):
    name = "hotelbeds"

    @classmethod
    def get_name(cls):
        return cls.name
