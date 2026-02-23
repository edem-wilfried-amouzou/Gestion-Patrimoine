from django.apps import AppConfig


class GestPatAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gest_Pat_App'

    def ready(self):
        import gest_Pat_App.signals  # charge les signaux