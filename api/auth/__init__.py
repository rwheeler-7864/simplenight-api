from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = "api.auth"
    label = "simplenight-auth"


default_app_config = "api.auth.AuthConfig"
