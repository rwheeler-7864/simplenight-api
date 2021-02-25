from api.hotel.adapters.adapter_info import AdapterInfo


class PricelineInfo(AdapterInfo):
    name = "priceline"

    @classmethod
    def get_name(cls):
        return cls.name
