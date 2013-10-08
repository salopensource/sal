from django.contrib import admin
from server.models import *
    
class BusinessUnitAdmin(admin.ModelAdmin):
    readonly_fields=('key',)
admin.site.register(UserProfile)
admin.site.register(BusinessUnit, BusinessUnitAdmin)
admin.site.register(MachineGroup)
admin.site.register(Machine)
admin.site.register(Fact)