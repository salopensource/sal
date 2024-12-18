from django.apps import AppConfig


class ServerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = "server"

    def ready(self):
        import server.signals
