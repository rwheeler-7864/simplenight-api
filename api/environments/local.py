from api.settings import *

LOGGING["root"] = {"handlers": ["console"], "level": "DEBUG"}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "simplenight",
        "USER": "simplenight",
        "PASSWORD": "simplenight",
        "HOST": "localhost",
        "PORT": "5432",
    },
}
