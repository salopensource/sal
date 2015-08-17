from django.contrib import admin
from inventory.models import Inventory, InventoryItem

class InventoryAdmin(admin.ModelAdmin):
    list_display = ('machine', 'datestamp', 'sha256hash')

class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'path')

admin.site.register(Inventory, InventoryAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)