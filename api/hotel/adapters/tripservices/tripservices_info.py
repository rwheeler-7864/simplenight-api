from api.hotel.adapters.adapter_info import AdapterInfo


class TripservicesInfo(AdapterInfo):
    name = "tripservices"

    @classmethod
    def get_name(cls):
        return cls.name
