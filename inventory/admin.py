from django.contrib import admin
from inventory.models import Application, Inventory, InventoryItem


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'bundleid', 'bundlename')
    search_fields = ('name', 'bundleid', 'bundlename')


class InventoryAdmin(admin.ModelAdmin):
    list_display = ('machine', 'datestamp', 'sha256hash')
    list_filter = ('datestamp',)
    date_hierarchy = 'datestamp'
    search_fields = ('machine__hostname',)


class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('application', 'version', 'path', 'machine')
    search_fields = ('application__name', 'version', 'machine__hostname')


admin.site.register(Application, ApplicationAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
