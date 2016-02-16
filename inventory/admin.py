from django.contrib import admin
from inventory.models import Inventory, InventoryItem


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'bundleid', 'bundlename')


class InventoryAdmin(admin.ModelAdmin):
    list_display = ('machine', 'datestamp', 'sha256hash')


class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'version', 'path')

    def get_name(self, item):
        return item.application.name


admin.site.register(Inventory, InventoryAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)