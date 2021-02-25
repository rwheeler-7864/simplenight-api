import decimal
import logging.config

from django.apps import AppConfig

from api.settings import LOGGING

logger = logging.getLogger(__name__)
logging.config.dictConfig(LOGGING)
logger.setLevel(logging.INFO)


class ApiConfig(AppConfig):
    name = "api"
    label = "api"

    def ready(self):
        decimal.getcontext().prec = 10
        decimal.getcontext().rounding = decimal.ROUND_HALF_DOWN


default_app_config = "api.ApiConfig"
