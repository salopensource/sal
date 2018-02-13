from django.contrib import admin
from licenses.models import License


class LicenseAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'cost_per_seat', 'total', 'used', 'available',
                    'inventory_filter')
    search_fields = ('item_name',)

    def inventory_filter(self, obj):
        filter_string = ''
        if obj.inventory_name:
            filter_string += "name: '%s' " % obj.inventory_name
        if obj.inventory_version:
            filter_string += "version: '%s' " % obj.inventory_version
        if obj.inventory_bundleid:
            filter_string += "bundleid: '%s' " % obj.inventory_bundleid
        if obj.inventory_bundlename:
            filter_string += "bundlename: '%s' " % obj.inventory_bundlename
        if obj.inventory_path:
            filter_string += "path: '%s' " % obj.inventory_path
        return filter_string


admin.site.register(License, LicenseAdmin)
