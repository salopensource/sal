from django.contrib import admin
from catalog.models import *


def business_unit(obj):
    return obj.machine_group.business_unit.name


class BusinessUnitFilter(admin.SimpleListFilter):
    title = 'Business Unit'
    parameter_name = 'business_unit'

    def lookups(self, request, model_admin):
        return ((bu.name, bu.name) for bu in BusinessUnit.objects.all())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(machine_group__business_unit__name=self.value())
        else:
            return queryset


class CatalogAdmin(admin.ModelAdmin):
    list_display = ('name', 'machine_group', business_unit)
    list_filter = ('machine_group', BusinessUnitFilter)
    search_fields = ('name',)


admin.site.register(Catalog, CatalogAdmin)
