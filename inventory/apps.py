from django.apps import AppConfig
from watson import search as watson

class InventoryAppConfig(AppConfig):
    name = "inventory"
    def ready(self):
        InventoryItem = self.get_model("InventoryItem")
        watson.register(InventoryItem)
