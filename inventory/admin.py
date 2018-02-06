from django.contrib import admin
from inventory.models import Application, Inventory, InventoryItem


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'bundleid', 'bundlename')


class InventoryAdmin(admin.ModelAdmin):
    list_display = ('machine', 'datestamp', 'sha256hash')


class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('application', 'version', 'path')


admin.site.register(Application, ApplicationAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
