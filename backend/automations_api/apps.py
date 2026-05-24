from django.apps import AppConfig


class AutomationsApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automations_api'

    def ready(self):
        from . import receivers  # noqa: F401
