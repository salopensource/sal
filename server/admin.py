from django.contrib import admin
from server.models import *
    
admin.site.register(UserProfile)
admin.site.register(BusinessUnit)
admin.site.register(MachineGroup)
admin.site.register(Machine)