from api.settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "simplenight-api-db",
        "USER": "simplenight",
        "PASSWORD": "y4yxYNqVj4s2XyY",
        "HOST": "35.193.80.3",
        "PORT": "5432",
        "OPTIONS": {
            "sslmode": "require",
            "sslrootcert": "api/secrets/prod/server-ca.crt",
            "sslcert": "api/secrets/prod/client-cert.pem",
            "sslkey": "api/secrets/prod/client-key.pem",
        },
    }
}
