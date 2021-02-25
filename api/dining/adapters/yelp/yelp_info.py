from api.dining.adapters.adapter_info import AdapterInfo


class YelpInfo(AdapterInfo):
    name = "yelp"

    @classmethod
    def get_name(cls):
        return cls.name
