import abc

from api.models.models import Provider


class AdapterInfo(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def get_name(cls):
        pass

    def get_or_create_provider_id(self):
        try:
            return Provider.objects.get(name=self.get_name())
        except Provider.DoesNotExist:
            provider = Provider(name=self.get_name())
            provider.save()
            return provider
