import abc


class BaseAdapter(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def factory(cls, test_mode=True):
        pass

    @classmethod
    @abc.abstractmethod
    def get_provider_name(cls):
        pass
