from django.contrib import admin
from server.models import *
    
class MachineGroupAdmin(admin.ModelAdmin):
    readonly_fields=('key',)
admin.site.register(UserProfile)
admin.site.register(BusinessUnit)
admin.site.register(MachineGroup, MachineGroupAdmin)
admin.site.register(Machine)
admin.site.register(Fact)
admin.site.register(PendingUpdate)
admin.site.register(PendingAppleUpdate)