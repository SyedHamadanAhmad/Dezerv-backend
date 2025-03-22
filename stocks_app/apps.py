from django.apps import AppConfig
# from .utils import initialise_db

class StocksAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stocks_app'

    # def ready(self):
    #     initialise_db()
